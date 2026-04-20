import csv
import io
import os
import re
import uuid
from collections import Counter
from datetime import date, datetime
from urllib.parse import unquote_plus

from constants.common_variables import LogLevels, Methods, StatusCodes
from psycopg2.extras import execute_values
from utils.auth_utils import AuthUtils
from utils.db_utils import DbUtils
from utils.logger import Logger
from utils.response import ResponseUtils
from utils.s3_utils import S3Utils

DEFAULT_UPLOAD_PREFIX = "control-metadata/"
DEFAULT_PRESIGNED_TTL_SECONDS = 900
DEFAULT_MAX_FILE_SIZE_MB = 20

FILE_EXTENSION_TO_FORMAT = {
    ".csv": "csv",
}

CONTENT_TYPE_TO_FORMAT = {
    "text/csv": "csv",
    "application/csv": "csv",
}

FORMAT_TO_CONTENT_TYPE = {
    "csv": "text/csv",
}

TRUE_VALUES = {"1", "true", "t", "yes", "y"}
FALSE_VALUES = {"0", "false", "f", "no", "n"}

FIELD_ALIASES = {
    "control_id": "vgcpid",
    "description": "description",
    "control_owner": "control_owner",
    "control_sme": "control_sme",
    "escalation_needed_yes_no": "escalation",
}

FIELD_TO_HEADER = {
    "vgcpid": "Control ID",
    "description": "Description",
    "control_owner": "Control Owner",
    "control_sme": "Control SME",
    "escalation": "Escalation Needed? (Yes / No)",
}

ALLOWED_CSV_COLUMNS = {
    "vgcpid",
    "description",
    "control_owner",
    "control_sme",
    "escalation",
}

REQUIRED_CSV_COLUMNS = {
    "vgcpid",
    "description",
    "control_owner",
    "control_sme",
    "escalation",
}

SUPPORTED_CSV_HEADERS = list(FIELD_TO_HEADER.values())


class ImportValidationError(Exception):
    pass


def get_int_env(name, default_value, minimum=1):
    raw_value = os.environ.get(name)
    if raw_value in (None, ""):
        return default_value

    try:
        parsed = int(raw_value)
        if parsed < minimum:
            return default_value
        return parsed
    except (TypeError, ValueError):
        return default_value


def resolve_file_format(filename, content_type=None):
    extension = os.path.splitext(filename or "")[1].lower()
    if extension in FILE_EXTENSION_TO_FORMAT:
        return FILE_EXTENSION_TO_FORMAT[extension]

    normalized_content_type = (content_type or "").split(";")[0].strip().lower()
    if normalized_content_type in CONTENT_TYPE_TO_FORMAT:
        return CONTENT_TYPE_TO_FORMAT[normalized_content_type]

    raise ImportValidationError(
        "Unsupported file type. Only CSV control metadata files are allowed."
    )


def build_upload_key(filename, file_format):
    upload_prefix = os.environ.get("UPLOAD_KEY_PREFIX", DEFAULT_UPLOAD_PREFIX)
    normalized_prefix = (upload_prefix or "").strip("/")
    if normalized_prefix:
        normalized_prefix = f"{normalized_prefix}/"

    normalized_filename = (filename or "").replace("\\", "/")
    safe_filename = os.path.basename(normalized_filename).strip().replace(" ", "_")
    if not safe_filename:
        safe_filename = f"controls-metadata.{file_format}"

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    unique_suffix = uuid.uuid4().hex
    return f"{normalized_prefix}{timestamp}-{unique_suffix}-{safe_filename}"


def parse_boolean(value, default_value, field_name):
    if value is None:
        return default_value

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return bool(value)

    normalized = str(value).strip().lower()
    if normalized == "":
        return default_value
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False

    raise ImportValidationError(f"{field_name} must be a boolean value")



def normalize_header_key(raw_key):
    header = str(raw_key or "").strip().lower()
    header = re.sub(r"[^a-z0-9]+", "_", header)
    header = re.sub(r"_+", "_", header).strip("_")
    return header


def normalize_row_keys(raw_row):
    normalized = {}
    for raw_key, raw_value in (raw_row or {}).items():
        if raw_key is None:
            continue
        normalized_key = normalize_header_key(raw_key)
        canonical_key = FIELD_ALIASES.get(normalized_key, normalized_key)
        normalized[canonical_key] = raw_value
    return normalized


def find_header_row_index(csv_rows):
    for row_index, row in enumerate(csv_rows):
        if any(str(cell or "").strip() for cell in row):
            return row_index
    return None


def validate_csv_header_row(header_row):
    canonical_columns = []
    unsupported_columns = []

    for cell in header_row:
        raw_header = str(cell or "").strip()
        if not raw_header:
            continue
        normalized = normalize_header_key(raw_header)
        canonical_key = FIELD_ALIASES.get(normalized)
        if canonical_key is None:
            unsupported_columns.append(raw_header)
            continue

        canonical_columns.append(canonical_key)

    if unsupported_columns:
        raise ImportValidationError(
            "CSV contains unsupported columns: "
            + ", ".join(sorted(set(unsupported_columns)))
            + ". Supported columns are: "
            + ", ".join(SUPPORTED_CSV_HEADERS)
            + "."
        )

    canonical_column_set = set(canonical_columns)

    unexpected_columns = sorted(canonical_column_set - ALLOWED_CSV_COLUMNS)
    if unexpected_columns:
        raise ImportValidationError(
            "CSV contains unsupported columns: "
            + ", ".join(unexpected_columns)
            + ". Supported columns are: "
            + ", ".join(SUPPORTED_CSV_HEADERS)
            + "."
        )

    missing_required_columns = REQUIRED_CSV_COLUMNS - canonical_column_set
    if missing_required_columns:
        missing_headers = [
            header
            for field, header in FIELD_TO_HEADER.items()
            if field in missing_required_columns
        ]
        raise ImportValidationError(
            "CSV header is missing required columns: " + ", ".join(missing_headers)
        )

    duplicate_columns = [
        FIELD_TO_HEADER[field]
        for field, count in Counter(canonical_columns).items()
        if count > 1
    ]
    if duplicate_columns:
        raise ImportValidationError(
            "CSV header contains duplicate columns: " + ", ".join(duplicate_columns)
        )


def to_control_tuple(raw_row, row_number):
    row = normalize_row_keys(raw_row)

    vgcpid = str(row.get("vgcpid", "")).strip()
    description = str(row.get("description", "")).strip()
    control_owner = str(row.get("control_owner") or "").strip()
    control_sme = (
        None
        if row.get("control_sme") is None
        else str(row.get("control_sme")).strip() or None
    )

    if not vgcpid:
        raise ImportValidationError(f"Row {row_number}: vgcpid is required")
    if not description:
        raise ImportValidationError(f"Row {row_number}: description is required")
    if not control_owner:
        raise ImportValidationError(f"Row {row_number}: control_owner is required")

    try:
        escalation = parse_boolean(
            row.get("escalation"), default_value=False, field_name="escalation"
        )
    except ImportValidationError as e:
        raise ImportValidationError(f"Row {row_number}: {str(e)}") from e

    # These fields are system-managed for template imports.
    is_active = True
    date_created = date.today()
    last_tested = None

    return (
        vgcpid,
        description,
        control_owner,
        control_sme,
        escalation,
        is_active,
        date_created,
        last_tested,
    )


def parse_csv_rows(file_bytes):
    try:
        decoded_csv = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        raise ImportValidationError("CSV file must be UTF-8 encoded") from e

    csv_rows = list(csv.reader(io.StringIO(decoded_csv)))
    if not csv_rows:
        raise ImportValidationError("CSV file is empty")

    header_row_index = find_header_row_index(csv_rows)
    if header_row_index is None:
        raise ImportValidationError(
            "CSV header row was not found. Expected columns: "
            + ", ".join(SUPPORTED_CSV_HEADERS)
            + "."
        )

    header_row = csv_rows[header_row_index]
    validate_csv_header_row(header_row)
    data_rows = csv_rows[header_row_index + 1 :]

    rows = []
    for row_number, row_values in enumerate(data_rows, start=header_row_index + 2):
        row_dict = {}
        for column_index, header_name in enumerate(header_row):
            if str(header_name or "").strip() == "":
                continue
            value = row_values[column_index] if column_index < len(row_values) else None
            row_dict[header_name] = value

        if not any(
            (str(value).strip() if value is not None else "")
            for value in row_dict.values()
        ):
            continue

        rows.append((row_number, row_dict))
    return rows


def parse_metadata_rows(file_bytes, file_format):
    if file_format == "csv":
        return parse_csv_rows(file_bytes)
    raise ImportValidationError("Unsupported file format")


def validate_and_transform_rows(rows):
    valid_rows = []
    invalid_rows = []

    for row_number, row in rows:
        try:
            valid_rows.append(to_control_tuple(row, row_number))
        except ImportValidationError as e:
            invalid_rows.append({"row": row_number, "error": str(e)})

    return valid_rows, invalid_rows


def dedupe_control_rows_by_vgcpid(control_rows):
    rows_by_vgcpid = {}
    duplicate_vgcpids = set()

    for row in control_rows:
        vgcpid = row[0]
        if vgcpid in rows_by_vgcpid:
            duplicate_vgcpids.add(vgcpid)
        rows_by_vgcpid[vgcpid] = row

    return list(rows_by_vgcpid.values()), sorted(duplicate_vgcpids)


def get_vgcpid_from_db_row(db_row):
    if isinstance(db_row, dict):
        return db_row.get("vgcpid")
    return db_row[0]


def bulk_insert_controls(control_rows):
    if not control_rows:
        return 0, []

    connection = DbUtils.get_db_connection()
    try:
        with connection.cursor() as cursor:
            input_vgcpids = [row[0] for row in control_rows]

            query = """
                INSERT INTO controls (
                    vgcpid,
                    description,
                    control_owner,
                    control_sme,
                    escalation,
                    is_active,
                    date_created,
                    last_tested
                ) VALUES %s
                ON CONFLICT (vgcpid) DO NOTHING
                RETURNING vgcpid
            """

            inserted_db_rows = execute_values(
                cursor,
                query,
                control_rows,
                page_size=500,
                fetch=True,
            )

            inserted_vgcpids = {
                vgcpid
                for vgcpid in (
                    get_vgcpid_from_db_row(db_row)
                    for db_row in (inserted_db_rows or [])
                )
                if vgcpid
            }
            existing_vgcpids = sorted(set(input_vgcpids) - inserted_vgcpids)
            inserted_rows = len(inserted_vgcpids)

            connection.commit()
            return inserted_rows, existing_vgcpids
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def process_import_file(bucket_name, object_key):
    max_file_size_mb = get_int_env(
        "IMPORT_MAX_FILE_SIZE_MB", DEFAULT_MAX_FILE_SIZE_MB, minimum=1
    )
    try:
        file_bytes, content_type = S3Utils.get_file_from_s3(
            bucket_name=bucket_name,
            object_key=object_key,
            max_file_size_mb=max_file_size_mb,
        )
    except ValueError as e:
        raise ImportValidationError(str(e)) from e

    file_format = resolve_file_format(object_key, content_type)
    parsed_rows = parse_metadata_rows(file_bytes, file_format)
    valid_rows, invalid_rows = validate_and_transform_rows(parsed_rows)
    deduped_valid_rows, duplicate_vgcpids = dedupe_control_rows_by_vgcpid(valid_rows)

    if duplicate_vgcpids:
        Logger.log(
            level=LogLevels.WARNING,
            message="Deduplicated repeated vgcpid values during import",
            extra_fields={
                "duplicate_vgcpid_count": len(duplicate_vgcpids),
                "duplicate_vgcpid_samples": duplicate_vgcpids[:10],
            },
        )

    if not deduped_valid_rows:
        raise ImportValidationError("No valid rows were found in the uploaded file")

    inserted_rows, existing_vgcpids = bulk_insert_controls(deduped_valid_rows)

    if existing_vgcpids:
        Logger.log(
            level=LogLevels.WARNING,
            message="Skipped vgcpid values that already exist in database",
            extra_fields={
                "existing_vgcpid_count": len(existing_vgcpids),
                "existing_vgcpid_samples": existing_vgcpids[:10],
            },
        )

    return {
        "bucket": bucket_name,
        "key": object_key,
        "file_format": file_format,
        "total_rows": len(parsed_rows),
        "valid_rows": len(valid_rows),
        "deduped_valid_rows": len(deduped_valid_rows),
        "duplicate_vgcpid_count": len(duplicate_vgcpids),
        "existing_vgcpid_count": len(existing_vgcpids),
        "invalid_rows": len(invalid_rows),
        "inserted_rows": inserted_rows,
        "invalid_row_samples": invalid_rows[:10],
    }


def process_s3_event(event):
    processed = []
    non_retryable_failures = []
    retryable_failures = []

    for record in event.get("Records", []):
        if record.get("eventSource") != "aws:s3":
            continue

        bucket_name = (record.get("s3") or {}).get("bucket", {}).get("name")
        object_key = unquote_plus(
            ((record.get("s3") or {}).get("object") or {}).get("key", "")
        )

        if not bucket_name or not object_key:
            non_retryable_failures.append(
                {
                    "bucket": bucket_name,
                    "key": object_key,
                    "error": "Missing S3 bucket or object key in event record",
                }
            )
            continue

        try:
            processed.append(process_import_file(bucket_name, object_key))
        except ImportValidationError as e:
            failure = {"bucket": bucket_name, "key": object_key, "error": str(e)}
            non_retryable_failures.append(failure)
            Logger.log(
                level=LogLevels.WARNING,
                message="Skipped invalid control metadata file",
                extra_fields=failure,
            )
        except Exception as e:
            failure = {"bucket": bucket_name, "key": object_key, "error": str(e)}
            retryable_failures.append(failure)
            Logger.log(
                level=LogLevels.ERROR,
                message="Retryable control metadata import failure",
                extra_fields=failure,
            )

    if retryable_failures:
        raise RuntimeError(
            "Failed to process "
            f"{len(retryable_failures)} import file(s) "
            "due to retryable errors"
        )

    summary = {
        "message": "Import processing completed",
        "processed_files": processed,
        "skipped_files": non_retryable_failures,
        "processed_count": len(processed),
        "skipped_count": len(non_retryable_failures),
    }
    return summary


def build_presigned_upload_response(body):
    bucket_name = os.environ.get("UPLOAD_BUCKET_NAME")
    if not bucket_name:
        raise RuntimeError("UPLOAD_BUCKET_NAME is not configured")

    requested_filename = str(
        body.get("filename") or body.get("file_name") or "controls-metadata.csv"
    ).strip()
    requested_content_type = body.get("content_type") or body.get("contentType")

    file_format = resolve_file_format(requested_filename, requested_content_type)
    upload_key = build_upload_key(requested_filename, file_format)
    ttl_seconds = get_int_env(
        "PRESIGNED_URL_TTL_SECONDS", DEFAULT_PRESIGNED_TTL_SECONDS, minimum=60
    )

    content_type = FORMAT_TO_CONTENT_TYPE[file_format]
    upload_url = S3Utils.generate_presigned_put_url(
        bucket_name=bucket_name,
        object_key=upload_key,
        content_type=content_type,
        expires_in=ttl_seconds,
    )

    return {
        "upload_url": upload_url,
        "bucket": bucket_name,
        "key": upload_key,
        "method": "PUT",
        "content_type": content_type,
        "required_headers": {"Content-Type": content_type},
        "expires_in": ttl_seconds,
    }


def lambda_handler(event, context):
    Logger.start()

    if S3Utils.is_s3_event(event):
        Logger.log(level=LogLevels.INFO, message="Import Function Started (S3)")
        return process_s3_event(event)

    Logger.log(level=LogLevels.INFO, message="Import Function Started (API)")

    try:
        if event is None or (hasattr(event, "__len__") and len(event) == 0):
            Logger.log(level=LogLevels.ERROR, message="No event data provided")
            return ResponseUtils.http_response(
                StatusCodes.BAD_REQUEST, {"error": "No event data provided"}
            )

        if event.get("httpMethod") == "OPTIONS":
            return ResponseUtils.cors_preflight()

        method, _ = ResponseUtils.get_method_and_path(event)
        method = (method or "").upper()

        if method != Methods.POST:
            return ResponseUtils.http_response(
                StatusCodes.METHOD_NOT_ALLOWED,
                {"error": f"Method {method} not allowed for import endpoint"},
            )

        if not AuthUtils.is_manager(event):
            return ResponseUtils.http_response(
                StatusCodes.FORBIDDEN,
                {"error": "Forbidden: Manager access required"},
            )

        try:
            request_body = ResponseUtils.get_json_body(event)
            response_payload = build_presigned_upload_response(request_body)
            return ResponseUtils.http_response(StatusCodes.OK, response_payload)
        except ImportValidationError as e:
            return ResponseUtils.http_response(
                StatusCodes.BAD_REQUEST,
                {"error": str(e)},
            )
    except Exception as e:
        Logger.log(
            level=LogLevels.ERROR,
            message="Error in import handler",
            extra_fields={"exception": str(e)},
        )
        return ResponseUtils.http_response(
            StatusCodes.INTERNAL_SERVER_ERROR,
            {"error": str(e)},
        )
