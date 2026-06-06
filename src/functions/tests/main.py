import json
from constants.common_variables import LogLevels, Methods, StatusCodes, TableNames
from functions.tests.test_repository import TestRepository
from utils.logger import Logger
from utils.response import ResponseUtils
from utils.auth_utils import AuthUtils
from utils.user_resolver import UserResolver


def _optional_request_id(body):
    request_id = body.get("request_id")
    if request_id == "":
        return None
    return request_id


def lambda_handler(event, context):
    if event and event.get("httpMethod") == "OPTIONS":
        return ResponseUtils.cors_preflight()

    Logger.start()

    if not event:
        Logger.log(level=LogLevels.ERROR, message="No event data provided")
        return ResponseUtils.http_response(
            StatusCodes.BAD_REQUEST, {"error": "No event data provided"}
        )

    try:
        TestRepository.set_audit_context(
            actor_user_id=UserResolver.resolve(event),
        )

        method, normalized_path = ResponseUtils.get_method_and_path(event)
        test_id = ResponseUtils.extract_id(event, normalized_path, TableNames.TESTS)

        if method == Methods.GET:
            # GET /tests/{test_id}
            if test_id:
                test_record = TestRepository.get_tests_by_id(test_id)
                if not test_record:
                    return ResponseUtils.http_response(
                        StatusCodes.NOT_FOUND, {"error": "Test not found"}
                    )
                return ResponseUtils.http_response(StatusCodes.OK, test_record)

            params = event.get("queryStringParameters") or {}
            request_id = params.get("request_id")
            control_id = params.get("control_id")
            details = str(params.get("details", "false")).lower() == "true"

            # GET /tests?request_id=X&details=true
            if request_id and details:
                records = TestRepository.get_tests_by_request_with_details(request_id)
            # GET /tests?request_id=X
            elif request_id:
                records = TestRepository.get_tests_by_request_id(request_id)
            # GET /tests?control_id=X
            elif control_id:
                records = TestRepository.get_tests_by_control_id(control_id)
            # GET /tests (All)
            else:
                records = TestRepository.get_all_tests()

            return ResponseUtils.http_response(StatusCodes.OK, records)

        if method == Methods.POST and normalized_path == "/tests":
            if not AuthUtils.is_manager(event):
                Logger.log(
                    level=LogLevels.WARNING,
                    message="Unauthorized test creation attempt",
                )
                return ResponseUtils.http_response(
                    StatusCodes.FORBIDDEN,
                    {"error": "Forbidden: Manager access required"},
                )

            body = json.loads(event.get("body", "{}"))
            required = [
                "vgcpid",
                "requires_dat",
                "requires_oet",
                "due_date",
                "description",
            ]

            missing = [k for k in required if k not in body]
            if missing:
                return ResponseUtils.http_response(
                    StatusCodes.BAD_REQUEST,
                    {"error": f"Missing required fields: {missing}"},
                )

            created = TestRepository.create(
                vgcpid=body["vgcpid"],
                request_id=_optional_request_id(body),
                description=body["description"],
                requires_dat=body["requires_dat"],
                requires_oet=body["requires_oet"],
                due_date=body["due_date"],
                assigned_tester_id=body.get("assigned_tester_id"),
                estimated_date=body.get("estimated_date"),
                evidence_links=body.get("evidence_links"),
            )

            if not created:
                return ResponseUtils.http_response(
                    StatusCodes.BAD_REQUEST,
                    {"error": "Failed to create test. Verify that VGCPID exists."},
                )

            return ResponseUtils.http_response(StatusCodes.OK, created)

        # PUT /tests/{test_id}
        if method == Methods.PUT:
            if not (AuthUtils.is_manager(event) or AuthUtils.is_tester(event)):
                Logger.log(
                    level=LogLevels.WARNING, message="Unauthorized test update attempt"
                )
                return ResponseUtils.http_response(
                    StatusCodes.FORBIDDEN,
                    {"error": "Forbidden: Manager or Tester access required"},
                )

            if not test_id:
                return ResponseUtils.http_response(
                    StatusCodes.BAD_REQUEST, {"error": "Test ID required for update"}
                )

            body = json.loads(event.get("body", "{}"))
            action = body.get("action")
            updated_record = None

            if action == "assign":
                tester_id = body.get("assigned_tester_id")
                if tester_id is None:
                    return ResponseUtils.http_response(
                        StatusCodes.BAD_REQUEST,
                        {"error": "assigned_tester_id is required"},
                    )
                updated_record = TestRepository.update_assigned_tester(
                    test_id, tester_id
                )
            elif action == "update_dat":
                updated_record = TestRepository.update_dat_track(
                    test_id, body.get("dat_step"), body.get("status")
                )
            elif action == "update_oet":
                updated_record = TestRepository.update_oet_track(
                    test_id, body.get("oet_step"), body.get("status")
                )
            elif action == "start":
                updated_record = TestRepository.start_test(test_id)
            elif action == "review":
                updated_record = TestRepository.review_test(test_id)
            elif action == "complete":
                updated_record = TestRepository.complete_test(test_id)
            elif action == "update_evidence_links":
                if "evidence_links" not in body:
                    return ResponseUtils.http_response(
                        StatusCodes.BAD_REQUEST,
                        {"error": "evidence_links is required"},
                    )
                evidence_links = body.get("evidence_links")
                if not isinstance(evidence_links, list):
                    return ResponseUtils.http_response(
                        StatusCodes.BAD_REQUEST,
                        {"error": "evidence_links must be a list"},
                    )
                updated_record = TestRepository.update_evidence_links(
                    test_id, evidence_links
                )
            elif action == "update_details":
                updated_record = TestRepository.update_details(
                    test_id,
                    body.get("vgcpid"),
                    _optional_request_id(body),
                    body.get("assigned_tester_id"),
                    body.get("requires_dat"),
                    body.get("requires_oet"),
                    body.get("due_date"),
                    body.get("estimated_date"),
                    body.get("description"),
                    body.get("evidence_links"),
                )
            elif action == "update_status":
                if "status" not in body:
                    return ResponseUtils.http_response(
                        StatusCodes.BAD_REQUEST,
                        {"error": "status is required for update_status action"},
                    )
                updated_record = TestRepository.update_status(
                    test_id, body.get("status")
                )
            else:
                return ResponseUtils.http_response(
                    StatusCodes.BAD_REQUEST, {"error": "Invalid or missing action"}
                )

            if not updated_record:
                return ResponseUtils.http_response(
                    StatusCodes.NOT_FOUND, {"error": "Test not found"}
                )

            return ResponseUtils.http_response(StatusCodes.OK, updated_record)

        # DELETE /tests/{test_id}
        if method == Methods.DELETE:
            if not AuthUtils.is_manager(event):
                Logger.log(
                    level=LogLevels.WARNING,
                    message="Unauthorized test deletion attempt",
                )
                return ResponseUtils.http_response(
                    StatusCodes.FORBIDDEN,
                    {"error": "Forbidden: Manager access required"},
                )

            if not test_id:
                return ResponseUtils.http_response(
                    StatusCodes.BAD_REQUEST, {"error": "Test ID required for deletion"}
                )

            params = event.get("queryStringParameters") or {}
            hard_delete = str(params.get("hard", "false")).lower() == "true"
            archive = str(params.get("archive", "true")).lower() != "false"

            if hard_delete:
                # Fetch the test only for hard delete to check COMPLETED constraint
                test_record = TestRepository.get_tests_by_id(test_id)
                if not test_record:
                    return ResponseUtils.http_response(
                        StatusCodes.NOT_FOUND, {"error": "Test not found"}
                    )

                current_status = test_record.get("status", "NOT_STARTED")

                # Check if status is COMPLETED - hard delete not allowed
                if current_status == "COMPLETED":
                    Logger.log(
                        level=LogLevels.WARNING,
                        message="Cannot hard delete completed test",
                        extra_fields={"test_id": test_id, "status": current_status},
                    )
                    return ResponseUtils.http_response(
                        StatusCodes.CONFLICT,
                        {
                            "error": "Cannot hard delete completed test. "
                            "Only archive/unarchive allowed.",
                            "test_id": test_id,
                            "status": current_status,
                        },
                    )

                deleted = TestRepository.hard_delete(test_id)
                if not deleted:
                    return ResponseUtils.http_response(
                        StatusCodes.NOT_FOUND, {"error": "Test not found"}
                    )

                Logger.log(
                    level=LogLevels.INFO,
                    message="Hard deleted test",
                    extra_fields={"test_id": test_id, "status": current_status},
                )
                return ResponseUtils.http_response(StatusCodes.OK, deleted)
            else:
                # Archive/unarchive path: no pre-fetch needed
                # soft_delete will return None if record doesn't exist
                deleted = TestRepository.soft_delete(test_id, archive=archive)
                if not deleted:
                    return ResponseUtils.http_response(
                        StatusCodes.NOT_FOUND, {"error": "Test not found"}
                    )

                action = "Archived" if archive else "Unarchived"
                Logger.log(
                    level=LogLevels.INFO,
                    message=f"{action} test",
                    extra_fields={
                        "test_id": test_id,
                        "status": deleted.get("status"),
                    },
                )
                return ResponseUtils.http_response(StatusCodes.OK, deleted)

        return ResponseUtils.http_response(
            StatusCodes.METHOD_NOT_ALLOWED, {"error": "Method not allowed"}
        )

    except Exception as e:
        error_message = str(e)
        # Catch missing vgcpid (Subquery returns NULL)
        if (
            "violates not-null constraint" in error_message
            and "control_id" in error_message
        ):
            Logger.log(
                level=LogLevels.WARNING,
                message="Invalid vgcpid provided",
                extra_fields={"exception": error_message},
            )
            return ResponseUtils.http_response(
                StatusCodes.BAD_REQUEST,
                {"error": "The provided vgcpid does not exist in the controls table."},
            )

        # Catch bad request_id or assigned_tester_id
        if "violates foreign key constraint" in error_message:
            Logger.log(
                level=LogLevels.WARNING,
                message="Foreign key violation",
                extra_fields={"exception": error_message},
            )
            return ResponseUtils.http_response(
                StatusCodes.BAD_REQUEST,
                {"error": "Invalid referenced ID provided."},
            )

        # Default Fallback
        Logger.log(
            level=LogLevels.ERROR,
            message="Error in tests handler",
            extra_fields={"exception": error_message},
        )
        return ResponseUtils.http_response(
            StatusCodes.INTERNAL_SERVER_ERROR, {"error": error_message}
        )
    finally:
        TestRepository.clear_audit_context()
