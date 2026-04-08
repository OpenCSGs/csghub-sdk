"""Behavior tests for CsgHubSandbox (HTTP mocked via httpx.MockTransport).

SDK maps HTTP failures to ``SandboxHttpError`` / ``SandboxTransportError`` (not raw httpx).
Does not cover ``exists`` (not implemented in SDK).
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import httpx
import pytest

from pycsghub.errors import SandboxHttpError
from pycsghub.sandbox_client import CsgHubSandboxConfig
from pycsghub.sandbox_client.client import CsgHubSandbox
from pycsghub.sandbox_client.models import SandboxCreateRequest, SandboxErrorResponse

from .conftest import (
    make_mock_transport,
    patch_async_client_with_transport,
    run_async,
    sample_httpbase_envelope,
    sample_runner_create_response,
    sample_sandbox_get_json,
    sample_v1_patch_success_json,
)


class TestCsgHubSandboxCreate:
    def test_when_api_returns_201_on_post_then_create_returns_id(
        self,
        csghub_sandbox_cfg_minimal: CsgHubSandboxConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "pycsghub.sandbox_client.client.get_token_to_send",
            lambda _token=None: "test-bearer-token",
        )
        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            assert request.method == "POST"
            assert str(request.url) == "http://sandbox-api.test/api/v1/sandboxes"
            assert request.headers.get("Authorization") == "Bearer test-bearer-token"
            body = json.loads(request.content)
            assert body["sandbox_name"] == "sandbox-x"
            assert body["image"] == "sandbox:test"
            assert body["resource_id"] == 1001
            assert body["port"] == 0
            return httpx.Response(
                201,
                json=sample_httpbase_envelope("Created", sample_runner_create_response(sandbox_id="sandbox-x")),
            )

        patch_async_client_with_transport(monkeypatch, make_mock_transport(handler))
        client = CsgHubSandbox(csghub_sandbox_cfg=csghub_sandbox_cfg_minimal, token="test-bearer-token")
        spec = SandboxCreateRequest(
            image="sandbox:test",
            resource_id=1001,
            sandbox_name="sandbox-x",
        )

        result = run_async(client.create_sandbox(spec))

        assert result.spec.sandbox_name == "sandbox-x"
        assert result.state.status == "Running"
        assert len(captured) == 1

    def test_when_explicit_token_then_bearer_uses_it(
        self,
        csghub_sandbox_cfg_minimal: CsgHubSandboxConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers.get("Authorization") == "Bearer ctx-hub-jwt"
            assert request.headers.get("Content-Type") == "application/json"
            return httpx.Response(
                201,
                json=sample_httpbase_envelope("Created", sample_runner_create_response(sandbox_id="sandbox-x")),
            )

        patch_async_client_with_transport(monkeypatch, make_mock_transport(handler))
        client = CsgHubSandbox(csghub_sandbox_cfg=csghub_sandbox_cfg_minimal, token="ctx-hub-jwt")
        spec = SandboxCreateRequest(
            image="sandbox:test",
            resource_id=1,
            sandbox_name="n",
        )
        run_async(client.create_sandbox(spec))

    def test_when_api_returns_4xx_then_raises_sandbox_http_error(
        self,
        csghub_sandbox_cfg_minimal: CsgHubSandboxConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "pycsghub.sandbox_client.client.get_token_to_send",
            lambda _token=None: "t",
        )

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                400,
                json={"error": "invalid request"},
            )

        patch_async_client_with_transport(monkeypatch, make_mock_transport(handler))
        client = CsgHubSandbox(csghub_sandbox_cfg=csghub_sandbox_cfg_minimal, token="t")
        spec = SandboxCreateRequest(
            image="sandbox:test",
            resource_id=1,
            sandbox_name="x",
        )

        with pytest.raises(SandboxHttpError) as exc_info:
            run_async(client.create_sandbox(spec))
        assert exc_info.value.status_code == 400


class TestSandboxErrorBodyParsing:
    def test_when_error_json_uses_msg_then_msg_is_returned(self) -> None:
        err = SandboxErrorResponse.model_validate_json('{"msg":"sandbox is starting"}')
        assert err.log_line() == "sandbox is starting"

    def test_when_error_json_has_code_and_msg_then_prefixed_string_is_returned(self) -> None:
        err = SandboxErrorResponse.model_validate_json('{"code":400,"msg":"sandbox is starting"}')
        assert err.log_line() == "400: sandbox is starting"


class TestSandboxApiV1OtherEndpoints:
    def test_get_sandbox_uses_doc_path_and_parses_body(
        self,
        csghub_sandbox_cfg_minimal: CsgHubSandboxConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "pycsghub.sandbox_client.client.get_token_to_send",
            lambda _token=None: "t",
        )

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "GET"
            assert str(request.url) == "http://sandbox-api.test/api/v1/sandboxes/sb-a"
            return httpx.Response(200, json=sample_sandbox_get_json(sandbox_name="sb-a"))

        patch_async_client_with_transport(monkeypatch, make_mock_transport(handler))
        client = CsgHubSandbox(csghub_sandbox_cfg=csghub_sandbox_cfg_minimal, token="t")
        result = run_async(client.get_sandbox("sb-a"))
        assert result.spec.sandbox_name == "sb-a"
        assert result.spec.image == "sandbox:test"

    def test_apply_sandbox_patches_by_name_and_accepts_200(
        self,
        csghub_sandbox_cfg_minimal: CsgHubSandboxConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "pycsghub.sandbox_client.client.get_token_to_send",
            lambda _token=None: "t",
        )

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "PATCH"
            assert str(request.url) == "http://sandbox-api.test/api/v1/sandboxes/sb-b"
            body = json.loads(request.content)
            assert "sandbox_name" not in body
            assert body["resource_id"] == 1001
            assert body["image"] == "img:latest"
            assert body["timeout"] == 600
            return httpx.Response(200, json=sample_v1_patch_success_json(sandbox_id="sb-b"))

        patch_async_client_with_transport(monkeypatch, make_mock_transport(handler))
        client = CsgHubSandbox(csghub_sandbox_cfg=csghub_sandbox_cfg_minimal, token="t")
        spec = SandboxCreateRequest(
            image="img:latest",
            resource_id=1001,
            sandbox_name="sb-b",
            timeout=600,
        )
        result = run_async(client.apply_sandbox(spec))
        assert result.spec.sandbox_name == "sb-b"
        assert result.state.status == "Running"

    def test_start_sandbox_puts_status_start(
        self,
        csghub_sandbox_cfg_minimal: CsgHubSandboxConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "pycsghub.sandbox_client.client.get_token_to_send",
            lambda _token=None: "t",
        )

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "PUT"
            assert str(request.url) == "http://sandbox-api.test/api/v1/sandboxes/sb-s/status/start"
            return httpx.Response(
                200,
                json=sample_httpbase_envelope("OK", sample_runner_create_response(sandbox_id="sb-s")),
            )

        patch_async_client_with_transport(monkeypatch, make_mock_transport(handler))
        client = CsgHubSandbox(csghub_sandbox_cfg=csghub_sandbox_cfg_minimal, token="t")
        result = run_async(client.start_sandbox("sb-s"))
        assert result.spec.sandbox_name == "sb-s"

    def test_stop_sandbox_puts_status_stop(
        self,
        csghub_sandbox_cfg_minimal: CsgHubSandboxConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "pycsghub.sandbox_client.client.get_token_to_send",
            lambda _token=None: "t",
        )
        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            assert request.method == "PUT"
            assert str(request.url) == "http://sandbox-api.test/api/v1/sandboxes/sb-t/status/stop"
            return httpx.Response(200, json={"msg": "OK"})

        patch_async_client_with_transport(monkeypatch, make_mock_transport(handler))
        client = CsgHubSandbox(csghub_sandbox_cfg=csghub_sandbox_cfg_minimal, token="t")
        run_async(client.stop_sandbox("sb-t"))
        assert len(captured) == 1


class TestSandboxLifecycleResponseLogging:
    def test_create_get_start_log_response_summary(
        self,
        csghub_sandbox_cfg_minimal: CsgHubSandboxConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "pycsghub.sandbox_client.client.get_token_to_send",
            lambda _token=None: "t",
        )

        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "POST" and request.url.path.endswith("/api/v1/sandboxes"):
                return httpx.Response(
                    201,
                    json=sample_httpbase_envelope("Created", sample_runner_create_response(sandbox_id="sb-log")),
                )
            if request.method == "GET" and request.url.path.endswith("/api/v1/sandboxes/sb-log"):
                return httpx.Response(200, json=sample_sandbox_get_json(sandbox_name="sb-log"))
            if request.method == "PUT" and request.url.path.endswith("/api/v1/sandboxes/sb-log/status/start"):
                return httpx.Response(
                    200,
                    json=sample_httpbase_envelope("OK", sample_runner_create_response(sandbox_id="sb-log")),
                )
            return httpx.Response(500, json={"error": "unexpected"})

        patch_async_client_with_transport(monkeypatch, make_mock_transport(handler))
        info_mock = MagicMock()
        monkeypatch.setattr("pycsghub.sandbox_client.client.logger.info", info_mock)
        client = CsgHubSandbox(csghub_sandbox_cfg=csghub_sandbox_cfg_minimal, token="t")

        spec = SandboxCreateRequest(image="sandbox:test", resource_id=1, sandbox_name="sb-log")
        run_async(client.create_sandbox(spec))
        run_async(client.get_sandbox("sb-log"))
        run_async(client.start_sandbox("sb-log"))

        all_calls = " ".join(str(call) for call in info_mock.call_args_list)
        assert "csg-sandbox-create" in all_calls and "response trace" in all_calls
        assert "csg-sandbox-get" in all_calls
        assert "csg-sandbox-start" in all_calls


class TestCsgHubSandboxStreamExecute:
    def test_when_stream_returns_lines_then_yields_non_empty_lines(
        self,
        csghub_sandbox_cfg_minimal: CsgHubSandboxConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "pycsghub.sandbox_client.client.get_token_to_send",
            lambda _token=None: "test-bearer-token",
        )
        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            assert request.method == "POST"
            assert str(request.url) == "http://sandbox-api.test/v1/sandboxes/my-sb/execute?port=8888"
            body = json.loads(request.content)
            assert body == {"command": "ls -l"}
            assert request.headers.get("Authorization") == "Bearer test-bearer-token"
            return httpx.Response(200, content=b"line1\nline2\n")

        patch_async_client_with_transport(monkeypatch, make_mock_transport(handler))
        client = CsgHubSandbox(csghub_sandbox_cfg=csghub_sandbox_cfg_minimal, token="test-bearer-token")

        async def _collect() -> list[str]:
            out: list[str] = []
            async for line in client.stream_execute_command("my-sb", "ls -l"):
                out.append(line)
            return out

        lines = run_async(_collect())
        assert lines == ["line1", "line2"]
        assert len(captured) == 1

    def test_when_aigateway_url_set_then_execute_uses_gateway_host(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "pycsghub.sandbox_client.client.get_token_to_send",
            lambda _token=None: "t",
        )
        cfg = CsgHubSandboxConfig.model_construct(
            base_url="http://starhub.test",
            aigateway_url="http://aigateway.test",
        )
        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            assert str(request.url) == "http://aigateway.test/v1/sandboxes/my-sb/execute?port=8888"
            return httpx.Response(200, content=b"ok\n")

        patch_async_client_with_transport(monkeypatch, make_mock_transport(handler))
        client = CsgHubSandbox(csghub_sandbox_cfg=cfg, token="t")

        async def _collect() -> list[str]:
            return [line async for line in client.stream_execute_command("my-sb", "echo")]

        lines = run_async(_collect())
        assert lines == ["ok"]
        assert len(captured) == 1

    def test_when_http_error_then_yields_error_prefix_not_raise(
        self,
        csghub_sandbox_cfg_minimal: CsgHubSandboxConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "pycsghub.sandbox_client.client.get_token_to_send",
            lambda _token=None: "t",
        )

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(400, content=b"bad")

        patch_async_client_with_transport(monkeypatch, make_mock_transport(handler))
        client = CsgHubSandbox(csghub_sandbox_cfg=csghub_sandbox_cfg_minimal, token="t")

        async def _collect() -> list[str]:
            return [line async for line in client.stream_execute_command("sb", "x")]

        lines = run_async(_collect())
        assert len(lines) == 1
        assert lines[0].startswith("ERROR: HTTP 400:")

    def test_when_request_error_then_yields_error_prefix(
        self,
        csghub_sandbox_cfg_minimal: CsgHubSandboxConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "pycsghub.sandbox_client.client.get_token_to_send",
            lambda _token=None: "t",
        )

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("no route", request=request)

        patch_async_client_with_transport(monkeypatch, make_mock_transport(handler))
        client = CsgHubSandbox(csghub_sandbox_cfg=csghub_sandbox_cfg_minimal, token="t")

        async def _collect() -> list[str]:
            return [line async for line in client.stream_execute_command("sb", "x")]

        lines = run_async(_collect())
        assert len(lines) == 1
        assert lines[0].startswith("ERROR: Request failed:")


class TestCsgHubSandboxFileEndpoints:
    def test_when_upload_file_then_posts_multipart_and_parses_message(
        self,
        csghub_sandbox_cfg_minimal: CsgHubSandboxConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "pycsghub.sandbox_client.client.get_token_to_send",
            lambda _token=None: "test-bearer-token",
        )

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "POST"
            assert str(request.url) == "http://sandbox-api.test/v1/sandboxes/sb-up/upload?port=8888"
            assert request.headers.get("Authorization") == "Bearer test-bearer-token"
            content_type = request.headers.get("Content-Type", "")
            assert content_type.startswith("multipart/form-data;")
            assert b'filename="hello.txt"' in request.content
            return httpx.Response(200, json={"message": "File 'hello.txt' uploaded successfully."})

        patch_async_client_with_transport(monkeypatch, make_mock_transport(handler))
        client = CsgHubSandbox(csghub_sandbox_cfg=csghub_sandbox_cfg_minimal, token="test-bearer-token")

        result = run_async(
            client.upload_file(
                sandbox_name="sb-up",
                file_name="hello.txt",
                file_bytes=b"hello world",
            ),
        )
        assert result.message == "File 'hello.txt' uploaded successfully."


class TestCsgHubSandboxStopAndBatch:
    def test_delete_sandbox_calls_put_status_stop(
        self,
        csghub_sandbox_cfg_minimal: CsgHubSandboxConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "pycsghub.sandbox_client.client.get_token_to_send",
            lambda _token=None: "test-bearer-token",
        )
        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            if request.method == "PUT" and request.url.path.endswith("/status/stop"):
                return httpx.Response(200, json={"msg": "OK", "data": None})
            return httpx.Response(500, json={"error": "unexpected"})

        patch_async_client_with_transport(monkeypatch, make_mock_transport(handler))
        client = CsgHubSandbox(csghub_sandbox_cfg=csghub_sandbox_cfg_minimal, token="test-bearer-token")
        run_async(client.delete_sandbox("my-sandbox"))
        assert len(captured) == 1
        assert captured[0].method == "PUT"
        assert captured[0].url.path.endswith("/api/v1/sandboxes/my-sandbox/status/stop")

    def test_upload_files_batch_posts_json(
        self,
        csghub_sandbox_cfg_minimal: CsgHubSandboxConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "pycsghub.sandbox_client.client.get_token_to_send",
            lambda _token=None: "test-bearer-token",
        )
        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            if request.method == "POST" and "/upload-files" in str(request.url):
                body = json.loads(request.content.decode())
                assert body["sandbox_name"] == "sb1"
                assert body["files"][0]["path"] == "a.txt"
                assert "content" in body["files"][0]
                return httpx.Response(200, json={"results": [{"path": "a.txt", "success": True, "error": ""}]})
            return httpx.Response(500, json={"error": "unexpected"})

        patch_async_client_with_transport(monkeypatch, make_mock_transport(handler))
        client = CsgHubSandbox(csghub_sandbox_cfg=csghub_sandbox_cfg_minimal, token="test-bearer-token")
        out = run_async(client.upload_files_batch("sb1", [("a.txt", b"hi")]))
        assert out["results"][0]["success"] is True
        assert "upload-files" in str(captured[0].url)
        assert "?port=8888" in str(captured[0].url)

    def test_download_files_batch_posts_json(
        self,
        csghub_sandbox_cfg_minimal: CsgHubSandboxConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "pycsghub.sandbox_client.client.get_token_to_send",
            lambda _token=None: "test-bearer-token",
        )
        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            if request.method == "POST" and "/download-files" in str(request.url):
                return httpx.Response(
                    200,
                    json={"results": [{"path": "a.txt", "content": "aGk=", "success": True, "error": ""}]},
                )
            return httpx.Response(500, json={"error": "unexpected"})

        patch_async_client_with_transport(monkeypatch, make_mock_transport(handler))
        client = CsgHubSandbox(csghub_sandbox_cfg=csghub_sandbox_cfg_minimal, token="test-bearer-token")
        out = run_async(client.download_files_batch("sb1", ["a.txt"]))
        assert out["results"][0]["success"] is True
        assert "download-files" in str(captured[0].url)
