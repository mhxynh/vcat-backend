from __future__ import annotations

import base64
import json
import sys
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BACKEND_URL = "http://localhost:3001"
FRONTEND_URL = "http://localhost:3000"
TIMEOUT_SECONDS = 20


@dataclass
class SmokeResult:
    name: str
    method: str
    path: str
    status: int | None
    elapsed_ms: int
    ok: bool
    summary: str


class SmokeClient:
    def __init__(self) -> None:
        self.headers = {"Authorization": f"Bearer {self._local_jwt()}"}
        self.results: list[SmokeResult] = []

    def request(
        self,
        name: str,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        expected: tuple[int, ...] = (200,),
    ) -> tuple[int | None, Any]:
        data = None
        headers = dict(self.headers)

        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        started_at = time.perf_counter()
        status = None
        content = ""

        try:
            request = Request(
                f"{BACKEND_URL}{path}",
                data=data,
                headers=headers,
                method=method,
            )
            with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                status = response.status
                content = response.read().decode("utf-8")
        except HTTPError as error:
            status = error.code
            content = error.read().decode("utf-8")
        except URLError as error:
            content = str(error)

        elapsed_ms = round((time.perf_counter() - started_at) * 1000)
        ok = status in expected
        self.results.append(
            SmokeResult(
                name=name,
                method=method,
                path=path,
                status=status,
                elapsed_ms=elapsed_ms,
                ok=ok,
                summary=content[:100],
            )
        )

        try:
            return status, json.loads(content) if content else None
        except json.JSONDecodeError:
            return status, content

    @staticmethod
    def _local_jwt() -> str:
        header = {"alg": "none", "typ": "JWT"}
        payload = {
            "sub": "docker-smoke-test",
            "email": "docker-smoke-test@example.com",
            "name": "Docker Smoke Test",
            "cognito:groups": ["Managers", "Testers"],
        }
        return ".".join(
            [
                _base64url_json(header),
                _base64url_json(payload),
                "signature",
            ]
        )


def _base64url_json(value: dict[str, Any]) -> str:
    raw = json.dumps(value, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def wait_for_url(url: str, timeout_seconds: int = 60) -> None:
    deadline = time.time() + timeout_seconds
    last_error = None

    while time.time() < deadline:
        try:
            with urlopen(url, timeout=5) as response:
                if response.status < 500:
                    return
        except Exception as error:
            last_error = error
        time.sleep(2)

    raise RuntimeError(f"{url} did not become reachable: {last_error}")


def first_row(payload: Any, label: str) -> dict[str, Any]:
    if not isinstance(payload, list) or not payload:
        raise RuntimeError(f"Expected at least one {label} row")
    if not isinstance(payload[0], dict):
        raise RuntimeError(f"Expected {label} rows to be objects")
    return payload[0]


def latest_by_field(
    rows: Any, field: str, value: Any, sort_field: str
) -> dict[str, Any]:
    if not isinstance(rows, list):
        raise RuntimeError(f"Expected rows list while looking for {field}={value}")

    matches = [row for row in rows if isinstance(row, dict) and row.get(field) == value]
    if not matches:
        raise RuntimeError(f"Could not find created row where {field}={value}")

    return sorted(matches, key=lambda row: row.get(sort_field) or 0, reverse=True)[0]


def cleanup(
    client: SmokeClient, temp_vgcpid: str | None, request_id: Any, test_id: Any
) -> None:
    if test_id:
        client.request(
            "cleanup test",
            "DELETE",
            f"/tests/{test_id}?hard=true",
            expected=(200, 404, 409),
        )
    if request_id:
        client.request(
            "cleanup request",
            "DELETE",
            f"/requests/{request_id}?hard=true",
            expected=(200, 404, 409),
        )
    if temp_vgcpid:
        client.request(
            "cleanup control",
            "DELETE",
            f"/controls/{temp_vgcpid}?hard=true",
            expected=(200, 404, 409),
        )


def run_smoke_test() -> list[SmokeResult]:
    client = SmokeClient()
    temp_vgcpid = None
    request_id = None
    test_id = None

    wait_for_url(FRONTEND_URL)
    wait_for_url(f"{BACKEND_URL}/controls")

    try:
        _, controls = client.request("GET controls list", "GET", "/controls")
        _, tests = client.request("GET tests list", "GET", "/tests")
        _, requests = client.request("GET requests list", "GET", "/requests")
        _, users = client.request("GET users active", "GET", "/users?is_active=true")

        control = first_row(controls, "control")
        test = first_row(tests, "test")
        request = first_row(requests, "request")
        user = first_row(users, "user")

        control_db_id = control["control_id"]
        control_id = control["vgcpid"]
        test_id_for_read = test["test_id"]
        request_id_for_read = request["request_id"]
        user_id = user["user_id"]

        client.request("GET control detail", "GET", f"/controls/{control_id}")
        client.request("GET test detail", "GET", f"/tests/{test_id_for_read}")
        client.request(
            "GET tests by request",
            "GET",
            f"/tests?request_id={request_id_for_read}&details=true",
        )
        client.request("GET tests by control", "GET", f"/tests?control_id={control_db_id}")
        client.request("GET request detail", "GET", f"/requests/{request_id_for_read}")
        client.request("GET comments list", "GET", "/comments")
        client.request(
            "GET comments by request",
            "GET",
            f"/comments?request_id={request_id_for_read}",
        )
        client.request("GET audit logs", "GET", "/audit")
        client.request("GET audit metrics", "GET", "/audit?view=metrics")
        client.request("GET user detail", "GET", f"/users/{user_id}")

        temp_vgcpid = f"DOCKER-SMOKE-{int(time.time())}"
        client.request(
            "POST control temp",
            "POST",
            "/controls",
            {
                "vgcpid": temp_vgcpid,
                "description": "Docker smoke test control",
                "control_owner": "Docker Smoke",
                "control_sme": "Docker Smoke",
                "escalation": False,
            },
        )
        client.request(
            "PUT control temp",
            "PUT",
            f"/controls/{temp_vgcpid}",
            {
                "description": "Docker smoke test control updated",
                "escalation": True,
                "is_active": True,
            },
        )
        client.request(
            "POST request temp",
            "POST",
            "/requests",
            {
                "requestor": "Docker Smoke",
                "due_date": "2026-12-31",
                "priority": "LOW",
                "description": "Docker smoke test request",
                "created_by": user_id,
            },
        )
        _, requests_after_create = client.request(
            "GET requests after temp create",
            "GET",
            "/requests",
        )
        created_request = latest_by_field(
            requests_after_create,
            "requestor",
            "Docker Smoke",
            "request_id",
        )
        request_id = created_request["request_id"]

        client.request(
            "PUT request temp",
            "PUT",
            f"/requests/{request_id}",
            {
                "priority": "MEDIUM",
                "requestor": "Docker Smoke",
                "due_date": "2026-12-31",
                "description": "Docker smoke test request updated",
            },
        )
        client.request(
            "POST test temp",
            "POST",
            "/tests",
            {
                "vgcpid": temp_vgcpid,
                "request_id": request_id,
                "requires_dat": True,
                "requires_oet": False,
                "due_date": "2026-12-31",
                "description": "Docker smoke test control test",
                "assigned_tester_id": user_id,
            },
        )
        _, tests_after_create = client.request(
            "GET tests after temp create", "GET", "/tests"
        )
        created_test = latest_by_field(
            tests_after_create, "vgcpid", temp_vgcpid, "test_id"
        )
        test_id = created_test["test_id"]

        client.request(
            "PUT test temp start", "PUT", f"/tests/{test_id}", {"action": "start"}
        )
        client.request(
            "POST comment temp",
            "POST",
            "/comments",
            {"test_id": test_id, "comment_text": "Docker smoke test comment"},
        )
        _, comments = client.request(
            "GET comments for temp test",
            "GET",
            f"/comments?test_id={test_id}",
        )
        comment = latest_by_field(
            comments,
            "comment_text",
            "Docker smoke test comment",
            "comment_id",
        )
        client.request(
            "DELETE comment temp",
            "DELETE",
            f"/comments?comment_id={comment['comment_id']}&test_id={test_id}",
        )
        client.request("DELETE test temp", "DELETE", f"/tests/{test_id}?hard=true")
        test_id = None
        client.request(
            "DELETE request temp", "DELETE", f"/requests/{request_id}?hard=true"
        )
        request_id = None
        client.request(
            "DELETE control temp", "DELETE", f"/controls/{temp_vgcpid}?hard=true"
        )
        temp_vgcpid = None

        client.request(
            "GET export controls",
            "GET",
            "/export?table=controls",
            expected=(200, 500),
        )
        client.request(
            "GET help media presign",
            "GET",
            "/help-media?key=docker-smoke.png",
            expected=(200, 500),
        )
        client.request(
            "POST import upload url",
            "POST",
            "/import",
            {"filename": "docker-smoke.csv", "content_type": "text/csv"},
            expected=(200, 500),
        )
        client.request(
            "DELETE user nonexistent safe",
            "DELETE",
            "/users/999999999",
            expected=(404,),
        )
    finally:
        cleanup(client, temp_vgcpid, request_id, test_id)

    return client.results


def print_results(results: list[SmokeResult]) -> None:
    print("\nDocker smoke test results")
    print("-" * 100)
    print(f"{'OK':<4} {'MS':>6} {'STATUS':>6} {'METHOD':<6} {'PATH':<42} NAME")
    print("-" * 100)

    for result in results:
        ok = "yes" if result.ok else "no"
        status = result.status if result.status is not None else "-"
        print(
            f"{ok:<4} {result.elapsed_ms:>6} {status:>6} "
            f"{result.method:<6} {result.path:<42} {result.name}"
        )


def main() -> int:
    try:
        results = run_smoke_test()
    except Exception as error:
        print(f"Docker smoke test failed before completion: {error}", file=sys.stderr)
        return 1

    print_results(results)
    failures = [result for result in results if not result.ok]
    if failures:
        print("\nFailures:")
        for failure in failures:
            print(f"- {failure.name}: HTTP {failure.status}, {failure.summary}")
        return 1

    print("\nDocker smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
