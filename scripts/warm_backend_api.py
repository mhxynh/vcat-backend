import json
import os
from pathlib import Path
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = "http://127.0.0.1:3001"
READY_MARKER = Path("/tmp/vcat-backend-warmed")
REQUEST_TIMEOUT_SECONDS = 180
SERVER_WAIT_SECONDS = 240


CORE_ROUTES = [
    ("GET", "/tests", None),
    ("GET", "/users?is_active=true", None),
    ("GET", "/controls", None),
]

ALL_ROUTES = [
    *CORE_ROUTES,
    ("GET", "/requests", None),
    ("GET", "/comments", None),
    ("GET", "/audit", None),
    ("GET", "/export", None),
    ("GET", "/help-media", None),
    (
        "POST",
        "/import",
        {"filename": "warmup.csv", "content_type": "text/csv"},
    ),
]


def get_routes() -> list[tuple[str, str, dict | None]]:
    mode = os.environ.get("WARM_BACKEND_ROUTES", "core").strip().lower()

    if mode in ("0", "false", "none", "off"):
        return []
    if mode == "all":
        return ALL_ROUTES
    if mode == "core":
        return CORE_ROUTES

    print(
        f"Unknown WARM_BACKEND_ROUTES={mode!r}; using core backend warmup.",
        flush=True,
    )
    return CORE_ROUTES


def wait_for_sam() -> None:
    deadline = time.time() + SERVER_WAIT_SECONDS
    while time.time() < deadline:
        try:
            request = Request(f"{BASE_URL}/tests", method="OPTIONS")
            with urlopen(request, timeout=5):
                return
        except Exception:
            time.sleep(2)

    raise TimeoutError("SAM local did not start accepting requests in time")


def warm_route(method: str, path: str, body: dict | None) -> None:
    data = None
    headers = {}

    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(
        f"{BASE_URL}{path}",
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            print(f"Warmed {method} {path}: HTTP {response.status}", flush=True)
    except HTTPError as error:
        # 4xx/5xx still means SAM loaded the Lambda image and invoked the route.
        print(f"Warmed {method} {path}: HTTP {error.code}", flush=True)
    except URLError as error:
        raise RuntimeError(f"Failed to warm {method} {path}: {error}") from error


def main() -> int:
    READY_MARKER.unlink(missing_ok=True)
    wait_for_sam()

    routes = get_routes()
    for method, path, body in routes:
        warm_route(method, path, body)

    READY_MARKER.write_text("Backend is ready for Docker local.\n")
    if routes:
        print(f"Backend API warmup complete ({len(routes)} route(s)).", flush=True)
    else:
        print("Backend API warmup skipped; SAM is accepting requests.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
