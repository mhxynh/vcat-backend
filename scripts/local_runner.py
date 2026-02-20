import argparse
import importlib
import json
import os
import sys
from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_ROOT = os.path.join(PROJECT_ROOT, "src")
LAYER_ROOT = os.path.join(SRC_ROOT, "functions", "common", "python")
for p in [PROJECT_ROOT, SRC_ROOT, LAYER_ROOT]:
    if p not in sys.path:
        sys.path.insert(0, p)

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

    print(f"\nStatus: {status}")
    print(f"Body:\n{body_str}")

if __name__ == "__main__":
    '''
    The argparse setup and main execution logic is included here to allow for easy local testing of Lambda functions with simulated API Gateway events. 
    This script can be run from the command line, specifying the Lambda function to invoke, the HTTP method, path parameters, and request body as needed. 
    The output will show the status code and response body in a readable format.
    '''
    parser = argparse.ArgumentParser(description="Invoke a Lambda locally with a simulated API Gateway event")
    parser.add_argument("--lambda-name", default="controls", help="Lambda function folder name (e.g., 'controls')")
    parser.add_argument("--method", default="GET", help="HTTP method")
    parser.add_argument("--vgcpid", default=None, help="Resource ID for /controls/{vgcpid}")
    # Body is provided for testing the POST /controls endpoint. Adjust as needed: "{"vgcpid": "VGCP-99999", "description": "Description for control 21", "control_owner": "Owner 67", "control_sme": "SME 5"}"
    parser.add_argument("--body", default=None, help="JSON body string for POST/PUT")
    parser.add_argument("--env", default="local", choices=["local", "prod"], help="Environment: local or prod (default: local)")
    args = parser.parse_args()

    # Load the appropriate .env file
    env_file = ".env.prod" if args.env == "prod" else ".env"
    load_dotenv(os.path.join(PROJECT_ROOT, env_file), override=True)
    print(f">>> Environment: {args.env} ({env_file})")

    # Build the path and path parameters
    base_path = f"/{args.lambda_name}"
    path_parameters = None

    if args.vgcpid:
        path = f"{base_path}/{args.vgcpid}"
        path_parameters = {"vgcpid": args.vgcpid}
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
