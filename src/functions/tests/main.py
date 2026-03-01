import json
from constants.common_variables import LogLevels, Methods, StatusCodes, TableNames
from utils.crud import CrudUtils
from functions.tests.test_repository import TestRepository
from utils.logger import Logger
from utils.response import ResponseUtils

def lambda_handler(event, context):
    Logger.start()

    if not event:
        Logger.log(level=LogLevels.ERROR, message="No event data provided")
        return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "No event data provided"})

    try:
        method, normalized_path = ResponseUtils.get_method_and_path(event)
        test_id = ResponseUtils.extract_id(event, normalized_path, TableNames.TESTS)
    
        if method == Methods.GET:
            # GET /tests/{test_id}: Get a single test by test_id
            if test_id:
                test_record = CrudUtils.get_by_id(TableNames.TESTS, "test_id", test_id)
                if not test_record:
                    return ResponseUtils.http_response(StatusCodes.NOT_FOUND, {"error": "Test not found"})
                return ResponseUtils.http_response(StatusCodes.OK, test_record)

            # GET /tests?request_id=X&details=true: Get tests by request_id with optional details
            params = event.get("queryStringParameters", {})
            request_id = params.get("request_id")
            control_id = params.get("control_id")
            details = str(params.get("details", "false")).lower() == "true"

            if request_id and details:
                records = TestRepository.get_tests_by_request_with_details(request_id)
            elif request_id:
                records = CrudUtils.get_by_filter(TableNames.TESTS, "request_id", request_id)
            elif control_id:
                records = CrudUtils.get_by_filter(TableNames.TESTS, "control_id", control_id)
            else:
                return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "Must provide request_id or control_id"})
                
            return ResponseUtils.http_response(StatusCodes.OK, records)

        # POST /tests : Create a new test
        if method == Methods.POST and normalized_path == "/tests":
            body = json.loads(event.get("body", "{}"))
            required = ["control_id", "request_id", "requires_dat", "requires_oet", "due_date"]
            
            if not all(k in body for k in required):
                return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "Missing required fields"})

            columns = required.copy()
            values = [body[k] for k in required]
            
            optional = ["assigned_tester_id", "estimated_date", "description"]
            for opt_field in optional:
                if opt_field in body:
                    columns.append(opt_field)
                    values.append(body[opt_field])
            
            created = CrudUtils.create(TableNames.TESTS, columns, values)
            return ResponseUtils.http_response(StatusCodes.OK, created)

        # PUT /tests/{test_id} : Update a test by test_id
        if method == Methods.PUT:
            if not test_id:
                return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "Test ID required for update"})

            body = json.loads(event.get("body", "{}"))
            action = body.get("action") 
            updated_record = None
            
            # Route specific actions to TestRepository
            if action == "update_dat":
                updated_record = TestRepository.update_dat_track(test_id, body.get("dat_step"), body.get("status"))
            elif action == "update_oet":
                updated_record = TestRepository.update_oet_track(test_id, body.get("oet_step"), body.get("status"))
            elif action == "start":
                updated_record = TestRepository.start_test(test_id)
            elif action == "review":
                updated_record = TestRepository.review_test(test_id)
            elif action == "complete":
                updated_record = TestRepository.complete_test(test_id)
            else:
                allowed_fields = ["assigned_tester_id", "status", "dat_step", "oet_step"]
                updates = {field: value for field, value in body.items() if field in allowed_fields}
                if updates:
                    updated_record = CrudUtils.update(TableNames.TESTS, "test_id", test_id, updates)

            if not updated_record:
                return ResponseUtils.http_response(StatusCodes.NOT_FOUND, {"error": "Test not found or invalid action provided"})
                
            return ResponseUtils.http_response(StatusCodes.OK, updated_record)

        # DELETE /tests/{test_id} : Delete a test by test_id
        if method == Methods.DELETE:
            if not test_id:
                return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "Test ID required for deletion"})
            
            deleted = CrudUtils.hard_delete(TableNames.TESTS, "test_id", test_id)
            if not deleted:
                return ResponseUtils.http_response(StatusCodes.NOT_FOUND, {"error": "Test not found"})
            
            return ResponseUtils.http_response(StatusCodes.OK, deleted)

        return ResponseUtils.http_response(StatusCodes.METHOD_NOT_ALLOWED, {"error": "Method not allowed"})

    except Exception as e:
        Logger.log(level=LogLevels.ERROR, message="Error in tests handler", extra_fields={"exception": str(e)})
        return ResponseUtils.http_response(StatusCodes.INTERNAL_SERVER_ERROR, {"error": str(e)})
    