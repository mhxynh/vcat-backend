import argparse
import importlib
import json
import os
import sys
from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_ROOT = os.path.join(PROJECT_ROOT, "src")
for p in [PROJECT_ROOT, SRC_ROOT]:
    if p not in sys.path:
        sys.path.insert(0, p)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

def build_event(method, path, path_parameters=None, body=None, query_params=None):
    return {
        "httpMethod": method,
        "path": path,
        "pathParameters": path_parameters,
        "queryStringParameters": query_params,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps(body) if body else None,
        "isBase64Encoded": False,
    }

def load_handler(lambda_name):
    module_path = f"functions.{lambda_name}.main"
    module = importlib.import_module(module_path)
    return module.lambda_handler

def format_output(response):
    status = response.get("statusCode", "?")
    body = response.get("body", "")
    
    try:
        parsed = json.loads(body)
        body_str = json.dumps(parsed, indent=2)
    except (json.JSONDecodeError, TypeError):
        body_str = body

    print(f"Status: {status}")
    print(f"Body:\n{body_str}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Invoke a Lambda locally with a simulated API Gateway event")
    parser.add_argument("--lambda-name", default="controls", help="Lambda function folder name (e.g., 'controls')")
    parser.add_argument("--method", default="GET", help="HTTP method (default: GET)")
    parser.add_argument("--id", default=None, help="Resource ID for /controls/{id}")
    parser.add_argument("--body", default=None, help="JSON body string for POST/PUT")
    args = parser.parse_args()

    # Build the path and path parameters
    base_path = f"/{args.lambda_name}"
    path_parameters = None

    if args.id:
        path = f"{base_path}/{args.id}"
        path_parameters = {"id": args.id}
    else:
        path = base_path

    # Parse body if provided
    body = None
    if args.body:
        body = json.loads(args.body)

    event = build_event(args.method, path, path_parameters, body)
    context = {}

    print(f">>> {args.method} {path}")
    print(f">>> Event: {json.dumps(event, indent=2)}\n")

    handler = load_handler(args.lambda_name)
    response = handler(event, context)
    format_output(response)
