import json
from unittest.mock import patch

import pytest


@patch("functions.users.main.ResponseUtils")
@patch("functions.users.main.Logger")
def test_options_returns_cors(mock_logger, mock_responseutils):
    mock_responseutils.cors_preflight.return_value = {"cors": True}
    from functions.users.main import lambda_handler

    event = {"httpMethod": "OPTIONS"}
    res = lambda_handler(event, None)
    assert res == {"cors": True}
    mock_responseutils.cors_preflight.assert_called_once()


@patch("functions.users.main.ResponseUtils")
@patch("functions.users.main.Logger")
def test_empty_event_returns_bad_request(mock_logger, mock_responseutils):
    from functions.users.main import lambda_handler

    mock_responseutils.cors_preflight.return_value = {"cors": True}
    mock_responseutils.http_response.return_value = {"status": 400}

    res = lambda_handler({}, None)
    assert res == {"status": 400}
    mock_responseutils.http_response.assert_called()


@patch("functions.users.main.CrudUtils")
@patch("functions.users.main.ResponseUtils")
@patch("functions.users.main.Logger")
def test_get_users_by_email_not_found(mock_logger, mock_responseutils, mock_crud):
    from functions.users.main import lambda_handler

    mock_responseutils.get_method_and_path.return_value = ("GET", "/users")
    mock_responseutils.extract_id.return_value = None
    mock_crud.get_by_filter.return_value = []
    mock_responseutils.http_response.return_value = {"status": 404}

    event = {"httpMethod": "GET", "queryStringParameters": {"email": "x@x"}}
    res = lambda_handler(event, None)
    assert res == {"status": 404}
    mock_crud.get_by_filter.assert_called_once()


@patch("functions.users.main.CrudUtils")
@patch("functions.users.main.ResponseUtils")
@patch("functions.users.main.Logger")
def test_get_users_by_email_found(mock_logger, mock_responseutils, mock_crud):
    from functions.users.main import lambda_handler

    mock_responseutils.get_method_and_path.return_value = ("GET", "/users")
    mock_crud.get_by_filter.return_value = ([{"user_id": 1}],)
    mock_responseutils.http_response.return_value = {"status": 200}

    event = {"httpMethod": "GET", "queryStringParameters": {"email": "x@x"}}
    res = lambda_handler(event, None)
    assert res == {"status": 200}


@patch("functions.users.main.AuthUtils")
@patch("functions.users.main.ResponseUtils")
@patch("functions.users.main.Logger")
def test_delete_requires_manager_and_handles_not_found(mock_logger, mock_responseutils, mock_auth):
    from functions.users.main import lambda_handler
    # Simulate not manager
    mock_auth.is_manager.return_value = False
    mock_responseutils.get_method_and_path.return_value = ("DELETE", "/users/123")
    mock_responseutils.extract_id.return_value = "123"
    mock_responseutils.http_response.return_value = {"status": 403}

    event = {"httpMethod": "DELETE"}
    res = lambda_handler(event, None)
    assert res == {"status": 403}
    mock_auth.is_manager.assert_called_once()


@patch("functions.users.main.AuthUtils")
@patch("functions.users.main.CrudUtils")
@patch("functions.users.main.ResponseUtils")
@patch("functions.users.main.Logger")
def test_delete_manager_deactivates_user_success(mock_logger, mock_responseutils, mock_crud, mock_auth):
    from functions.users.main import lambda_handler
    mock_auth.is_manager.return_value = True
    mock_responseutils.get_method_and_path.return_value = ("DELETE", "/users/123")
    mock_responseutils.extract_id.return_value = "123"
    mock_crud.deactivate.return_value = {"user_id": "123", "is_active": False}
    mock_responseutils.http_response.return_value = {"status": 200}

    event = {"httpMethod": "DELETE"}
    res = lambda_handler(event, None)
    assert res == {"status": 200}
    mock_crud.deactivate.assert_called_once()
