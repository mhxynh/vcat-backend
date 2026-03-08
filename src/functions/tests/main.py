import json
from constants.common_variables import LogLevels, Methods, StatusCodes, TableNames
from functions.tests.test_repository import TestRepository
from utils.logger import Logger
from utils.response import ResponseUtils
from utils.auth_utils import AuthUtils

def lambda_handler(event, context):
    if event and event.get("httpMethod") == "OPTIONS":
        return ResponseUtils.cors_preflight()

    Logger.start()

    if not event:
        Logger.log(level=LogLevels.ERROR, message="No event data provided")
        return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "No event data provided"})

    try:
        body_for_context = ResponseUtils.get_json_body(event)
        TestRepository.set_audit_context(
            actor_user_id=ResponseUtils.get_actor_user_id(event, body=body_for_context),
        )

        method, normalized_path = ResponseUtils.get_method_and_path(event)
        test_id = ResponseUtils.extract_id(event, normalized_path, TableNames.TESTS)
    
        if method == Methods.GET:
            # GET /tests/{test_id}
            if test_id:
                test_record = TestRepository.get_tests_by_id(test_id)
                if not test_record:
                    return ResponseUtils.http_response(StatusCodes.NOT_FOUND, {"error": "Test not found"})
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
                Logger.log(level=LogLevels.WARNING, message="Unauthorized test creation attempt")
                return ResponseUtils.http_response(StatusCodes.FORBIDDEN, {"error": "Forbidden: Manager access required"})

            body = json.loads(event.get("body", "{}"))
            required = ["vgcpid", "request_id", "requires_dat", "requires_oet", "due_date", "description"]
            
            missing = [k for k in required if k not in body]
            if missing:
                return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": f"Missing required fields: {missing}"})
            
            created = TestRepository.create(
                vgcpid = body["vgcpid"],
                request_id = body["request_id"],
                description = body["description"],
                requires_dat = body["requires_dat"],
                requires_oet = body["requires_oet"],
                due_date = body["due_date"],
                assigned_tester_id = body.get("assigned_tester_id"),
                estimated_date = body.get("estimated_date")
            )

            if not created:
                return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "Failed to create test. Verify that VGCPID exists."})
            
            return ResponseUtils.http_response(StatusCodes.OK, created)

        # PUT /tests/{test_id}
        if method == Methods.PUT:
            if not (AuthUtils.is_manager(event) or AuthUtils.is_tester(event)):
                Logger.log(level=LogLevels.WARNING, message="Unauthorized test update attempt")
                return ResponseUtils.http_response(StatusCodes.FORBIDDEN, {"error": "Forbidden: Manager or Tester access required"})

            if not test_id:
                return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "Test ID required for update"})

            body = json.loads(event.get("body", "{}"))
            action = body.get("action") 
            updated_record = None
            
            if action == "assign":
                tester_id = body.get("assigned_tester_id")
                if tester_id is None:
                    return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "assigned_tester_id is required"})
                updated_record = TestRepository.update_assigned_tester(test_id, tester_id)
            elif action == "update_dat":
                updated_record = TestRepository.update_dat_track(test_id, body.get("dat_step"), body.get("status"))
            elif action == "update_oet":
                updated_record = TestRepository.update_oet_track(test_id, body.get("oet_step"), body.get("status"))
            elif action == "start":
                updated_record = TestRepository.start_test(test_id)
            elif action == "review":
                updated_record = TestRepository.review_test(test_id)
            elif action == "complete":
                updated_record = TestRepository.complete_test(test_id)
            elif action == "update_details":
                updated_record = TestRepository.update_details(
                    test_id,
                    body.get("vgcpid"),
                    body.get("request_id"),
                    body.get("assigned_tester_id"),
                    body.get("requires_dat"),
                    body.get("requires_oet"),
                    body.get("due_date"),
                    body.get("estimated_date"),
                    body.get("description")
                )
            else:
                return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "Invalid or missing action"})

            if not updated_record:
                return ResponseUtils.http_response(StatusCodes.NOT_FOUND, {"error": "Test not found"})
                
            return ResponseUtils.http_response(StatusCodes.OK, updated_record)

        # DELETE /tests/{test_id}
        if method == Methods.DELETE:
            if not AuthUtils.is_manager(event):
                Logger.log(level=LogLevels.WARNING, message="Unauthorized test deletion attempt")
                return ResponseUtils.http_response(StatusCodes.FORBIDDEN, {"error": "Forbidden: Manager access required"})

            if not test_id:
                return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "Test ID required for deletion"})
            
            params = event.get("queryStringParameters") or {}
            hard_delete = str(params.get("hard", "false")).lower() == "true"
            
            if hard_delete:
                deleted = TestRepository.hard_delete(test_id)
            else:
                deleted = TestRepository.soft_delete(test_id)

            if not deleted:
                return ResponseUtils.http_response(StatusCodes.NOT_FOUND, {"error": "Test not found"})
            
            return ResponseUtils.http_response(StatusCodes.OK, deleted)

        return ResponseUtils.http_response(StatusCodes.METHOD_NOT_ALLOWED, {"error": "Method not allowed"})

    except Exception as e:
        error_message = str(e)
        # Catch missing vgcpid (Subquery returns NULL)
        if "violates not-null constraint" in error_message and "control_id" in error_message:
             Logger.log(level=LogLevels.WARNING, message="Invalid vgcpid provided", extra_fields={"exception": error_message})
             return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "The provided vgcpid does not exist in the controls table."})
             
        # Catch bad request_id or assigned_tester_id
        if "violates foreign key constraint" in error_message:
             Logger.log(level=LogLevels.WARNING, message="Foreign key violation", extra_fields={"exception": error_message})
             return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "Invalid referenced ID (e.g., request_id or assigned_tester_id) provided."})
             
        # Default Fallback
        Logger.log(level=LogLevels.ERROR, message="Error in tests handler", extra_fields={"exception": error_message})
        return ResponseUtils.http_response(StatusCodes.INTERNAL_SERVER_ERROR, {"error": error_message})
    finally:
        TestRepository.clear_audit_context()
