import os
from urllib.parse import unquote

from constants.common_variables import Methods, StatusCodes
from utils.response import ResponseUtils
from utils.s3_utils import S3Utils

ALLOWED_EXTENSIONS = {".gif", ".mp4", ".png", ".jpg", ".jpeg", ".webp"}
DEFAULT_TTL_SECONDS = 900


def get_config():
    bucket_name = os.environ.get("HELP_MEDIA_BUCKET_NAME", "")
    ttl_seconds = int(
        os.environ.get("HELP_MEDIA_PRESIGNED_URL_TTL_SECONDS", DEFAULT_TTL_SECONDS)
    )
    return bucket_name, ttl_seconds


def normalize_media_key(value):
    key = unquote(str(value or "")).strip()
    if key.startswith("/help-assets/"):
        key = key[len("/help-assets/") :]
    key = key.lstrip("/")

    if not key or ".." in key.split("/"):
        return None

    _, extension = os.path.splitext(key.lower())
    if extension not in ALLOWED_EXTENSIONS:
        return None

    return key


def lambda_handler(event, context):
    method, _path = ResponseUtils.get_method_and_path(event or {})

    if method != Methods.GET:
        return ResponseUtils.http_response(
            StatusCodes.METHOD_NOT_ALLOWED,
            {"error": "Method not allowed"},
        )

    bucket_name, ttl_seconds = get_config()
    if not bucket_name:
        return ResponseUtils.http_response(
            StatusCodes.INTERNAL_SERVER_ERROR,
            {"error": "Help media bucket is not configured"},
        )

    params = ResponseUtils.get_query_params(event or {})
    media_key = normalize_media_key(params.get("key"))
    if not media_key:
        return ResponseUtils.http_response(
            StatusCodes.BAD_REQUEST,
            {"error": "A valid help media key is required"},
        )

    url = S3Utils.generate_presigned_get_url(
        bucket_name=bucket_name,
        object_key=media_key,
        expires_in=ttl_seconds,
    )

    return ResponseUtils.http_response(
        StatusCodes.OK,
        {
            "url": url,
            "key": media_key,
            "expires_in": ttl_seconds,
        },
    )
