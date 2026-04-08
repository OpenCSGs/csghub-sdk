"""Async HTTP client for CSGHub sandbox APIs (Starhub EE/SaaS + sandbox-runtime proxy).

This module implements two *families* of endpoints:

* **Lifecycle (JSON)** — Under ``{base_url}/api/v1/sandboxes``: create, read, patch configuration,
  start/stop. Responses typically wrap payloads in an ``httpbase`` envelope (``{"msg","data"}``);
  the client unwraps ``data`` into :class:`~pycsghub.sandbox_client.models.SandboxResponse`.
* **Runtime (gateway)** — Under ``{aigateway_url}/v1/sandboxes/...`` when ``aigateway_url`` is set,
  else the same host as ``base_url``: stream shell output, upload files, batch upload/download,
  and lightweight health checks. These paths use ``?port=8888`` as required by the gateway.

**Errors:** Non-2xx lifecycle calls raise :class:`~pycsghub.errors.SandboxHttpError` or
:class:`~pycsghub.errors.SandboxTransportError`; malformed JSON raises
:class:`~pycsghub.errors.SandboxResponseParseError`. :meth:`CsgHubSandbox.stream_execute_command`
does *not* raise on failure: it yields a single ``ERROR: ...`` line (compatible with Genius-style callers).

**Auth:** Bearer token via ``token=`` or the same resolution as the rest of the SDK
(``get_token_to_send`` / ``CSGHUB_TOKEN``).
"""

from __future__ import annotations

import base64
import json
import logging
from typing import Any, Dict, Optional

import httpx
from pydantic import ValidationError

from pycsghub.errors import SandboxHttpError, SandboxResponseParseError, SandboxTransportError
from pycsghub.sandbox_client.config import CsgHubSandboxConfig
from pycsghub.sandbox_client.models import (
    SandboxCreateRequest,
    SandboxErrorResponse,
    SandboxResponse,
    SandboxUpdateConfigRequest,
    SandboxUploadFileResponse,
)
from pycsghub.utils import get_token_to_send

try:
    from collections.abc import AsyncGenerator
except ImportError:
    from typing import AsyncGenerator

logger = logging.getLogger(__name__)

# Default timeout for lifecycle JSON calls (create, get, patch, start/stop).
_TIMEOUT = 60.0


def _api_sandboxes_root(cfg: CsgHubSandboxConfig) -> str:
    """Return the collection URL for sandbox lifecycle APIs."""
    base = cfg.base_url.removesuffix("/")
    return f"{base}/api/v1/sandboxes"


def _aigateway_base(cfg: CsgHubSandboxConfig) -> str:
    """Base URL for ``/v1/sandboxes/...`` runtime routes; falls back to ``base_url`` if unset."""
    raw = (cfg.aigateway_url or "").strip()
    return raw.removesuffix("/") if raw else cfg.base_url.removesuffix("/")


def _dump_create_body(spec: SandboxCreateRequest) -> dict[str, Any]:
    """Serialize create request: omit nulls; use JSON field aliases."""
    return spec.model_dump(mode="json", exclude_none=True, by_alias=True)


def _dump_update_config_body(body: SandboxUpdateConfigRequest) -> dict[str, Any]:
    """Serialize PATCH body: omit nulls and defaults (Go ``omitempty`` parity)."""
    return body.model_dump(mode="json", exclude_none=True, exclude_defaults=True, by_alias=True)


def _log_error_body(text: str) -> str:
    """Best-effort parse of error JSON for logging; falls back to a truncated raw body."""
    try:
        err = SandboxErrorResponse.model_validate_json(text)
        return err.log_line()
    except Exception:
        return text[:500]


def _parse_sandbox_response_json(body: object) -> SandboxResponse:
    """Parse ``SandboxResponse`` from a bare object or ``httpbase`` ``{"data": ...}`` envelope."""
    try:
        if not isinstance(body, dict):
            msg = "sandbox API response must be a JSON object"
            raise TypeError(msg)
        if "spec" in body and "state" in body:
            return SandboxResponse.model_validate(body)
        if "data" in body:
            inner = body["data"]
            if inner is None:
                msg = "sandbox API response has data: null"
                raise ValueError(msg)
            return SandboxResponse.model_validate(inner)
        return SandboxResponse.model_validate(body)
    except (TypeError, ValueError, ValidationError) as e:
        raise SandboxResponseParseError(str(e), detail=str(e)) from e


def _log_lifecycle_response(
    *,
    span_name: str,
    trace_label: str,
    response: SandboxResponse,
) -> None:
    """Structured INFO line after successful create/get/start/update."""
    logger.info(
        "[CsgHubSandbox] %s response trace=%s sandbox_name=%s status=%s image=%s",
        span_name,
        trace_label,
        response.spec.sandbox_name,
        response.state.status,
        response.spec.image,
    )


def _transport_error(e: httpx.RequestError) -> SandboxTransportError:
    """Wrap httpx transport failures with optional request URL for debugging."""
    req = e.request
    url = str(req.url) if req is not None else None
    return SandboxTransportError(str(e), request_url=url)


class CsgHubSandbox:
    """Async facade for sandbox lifecycle and runtime HTTP APIs.

    Parameters
    ----------
    csghub_sandbox_cfg
        Hub and optional AI Gateway bases. Defaults match the public Hub (see
        :class:`~pycsghub.sandbox_client.config.CsgHubSandboxConfig`).
    token
        Explicit bearer token. If omitted, :func:`~pycsghub.utils.get_token_to_send` supplies one
        from environment or token file (same behavior as other SDK entry points).
    """

    def __init__(
        self,
        csghub_sandbox_cfg: Optional[CsgHubSandboxConfig] = None,
        *,
        token: Optional[str] = None,
    ) -> None:
        self._cfg = csghub_sandbox_cfg if csghub_sandbox_cfg is not None else CsgHubSandboxConfig()
        self._token = token

    def _bearer(self) -> Optional[str]:
        return get_token_to_send(self._token)

    def _headers(self) -> dict[str, str]:
        bearer = self._bearer()
        return {
            "Authorization": f"Bearer {bearer}",
            "Content-Type": "application/json",
        }

    def _auth_headers(self) -> dict[str, str]:
        bearer = self._bearer()
        return {"Authorization": f"Bearer {bearer}"}

    def _root(self) -> str:
        return _api_sandboxes_root(self._cfg)

    def _execute_stream_url(self, sandbox_name: str) -> str:
        base = _aigateway_base(self._cfg)
        return f"{base}/v1/sandboxes/{sandbox_name}/execute?port=8888"

    def _upload_url(self, sandbox_name: str) -> str:
        base = _aigateway_base(self._cfg)
        return f"{base}/v1/sandboxes/{sandbox_name}/upload?port=8888"

    def _runtime_health_url(self, sandbox_name: str) -> str:
        base = _aigateway_base(self._cfg)
        return f"{base}/v1/sandboxes/{sandbox_name}/?port=8888"

    def _upload_files_batch_url(self, sandbox_name: str) -> str:
        base = _aigateway_base(self._cfg)
        return f"{base}/v1/sandboxes/{sandbox_name}/upload-files?port=8888"

    def _download_files_batch_url(self, sandbox_name: str) -> str:
        base = _aigateway_base(self._cfg)
        return f"{base}/v1/sandboxes/{sandbox_name}/download-files?port=8888"

    async def stream_execute_command(
        self,
        sandbox_name: str,
        command: str,
        *,
        timeout: float = 1800.0,
    ) -> AsyncGenerator[str, None]:
        """Stream stdout/stderr as newline-delimited chunks from the sandbox runtime.

        Calls ``POST .../v1/sandboxes/{sandbox_name}/execute?port=8888`` with body
        ``{"command": "<shell>"}``. Empty lines are skipped.

        On HTTP or transport failure, yields exactly one line starting with ``ERROR:`` and does
        **not** raise (callers that expect exceptions should wrap this generator).

        Parameters
        ----------
        timeout
            Per-request timeout in seconds (default 30 minutes for long-running commands).
        """
        url = self._execute_stream_url(sandbox_name)
        payload = {"command": command}
        try:
            async with (
                # trust_env=False: do not pick up ambient proxy env vars; keeps routing predictable.
                httpx.AsyncClient(trust_env=False, timeout=timeout) as client,
                client.stream("POST", url, headers=self._headers(), json=payload) as response,
            ):
                response.raise_for_status()

                full_output: list[str] = []
                async for line in response.aiter_lines():
                    if line:
                        full_output.append(line)
                        yield line
                if full_output:
                    complete_output = "\n".join(full_output)
                    truncated_output = "\n".join(
                        [line[:100] + "..." if len(line) > 100 else line for line in full_output[:5]],
                    ) + ("\n..." if len(full_output) > 5 else "")
                    logger.debug(
                        "[CsgHubSandbox] exec-command output lines=%s length=%s sample=%s",
                        len(full_output),
                        len(complete_output),
                        truncated_output[:200],
                    )
        except httpx.HTTPStatusError as e:
            try:
                await e.response.aread()
                err_body = e.response.text
            except Exception as read_err:
                logger.warning(
                    "Sandbox exec HTTP error body unreadable for %s: %s",
                    sandbox_name,
                    read_err,
                )
                err_body = ""
            logger.error(
                "Sandbox exec failed: HTTP %s for %s: %s",
                e.response.status_code,
                sandbox_name,
                err_body,
            )
            yield f"ERROR: HTTP {e.response.status_code}: {err_body}"
        except httpx.RequestError as e:
            logger.error("Sandbox exec request failed for %s: %s", sandbox_name, e)
            yield f"ERROR: Request failed: {e}"

    async def create_sandbox(self, spec: SandboxCreateRequest) -> SandboxResponse:
        """Create a sandbox; expects HTTP 201 and a ``SandboxResponse`` in the envelope."""
        resp = await self._raw_request(
            span_name="csg-sandbox-create",
            method="POST",
            url=self._root(),
            json_body=_dump_create_body(spec),
            success_statuses=(201,),
            timeout=_TIMEOUT,
            trace_label=spec.sandbox_name,
        )
        body = _response_json(resp)
        parsed = _parse_sandbox_response_json(body)
        _log_lifecycle_response(
            span_name="csg-sandbox-create",
            trace_label=spec.sandbox_name,
            response=parsed,
        )
        return parsed

    async def delete_sandbox(self, sandbox_id: str) -> None:
        """Tear down resources: alias for :meth:`stop_sandbox` (no HTTP ``DELETE`` on Starhub)."""
        await self.stop_sandbox(sandbox_id)

    async def upload_files_batch(
        self,
        sandbox_name: str,
        files: list[tuple[str, bytes]],
        *,
        timeout: float = 120.0,
    ) -> dict[str, Any]:
        """Upload many files in one JSON request (base64 contents) via the gateway proxy."""
        url = self._upload_files_batch_url(sandbox_name)
        payload: dict[str, Any] = {
            "sandbox_name": sandbox_name,
            "files": [{"path": path, "content": base64.b64encode(content).decode("ascii")} for path, content in files],
        }
        resp = await self._raw_request(
            span_name="csg-sandbox-upload-files-batch",
            method="POST",
            url=url,
            json_body=payload,
            success_statuses=(200,),
            timeout=timeout,
            trace_label=sandbox_name,
        )
        return _response_json(resp)

    async def download_files_batch(
        self,
        sandbox_name: str,
        paths: list[str],
        *,
        timeout: float = 120.0,
    ) -> dict[str, Any]:
        """Download many paths in one JSON request; response shape is server-defined (dict)."""
        url = self._download_files_batch_url(sandbox_name)
        payload: dict[str, Any] = {
            "sandbox_name": sandbox_name,
            "files": [{"path": p} for p in paths],
        }
        resp = await self._raw_request(
            span_name="csg-sandbox-download-files-batch",
            method="POST",
            url=url,
            json_body=payload,
            success_statuses=(200,),
            timeout=timeout,
            trace_label=sandbox_name,
        )
        return _response_json(resp)

    async def upload_file(
        self,
        sandbox_name: str,
        file_name: str,
        file_bytes: bytes,
        *,
        timeout: float = _TIMEOUT,
    ) -> SandboxUploadFileResponse:
        """Upload a single file via ``multipart/form-data`` field ``file`` (not JSON)."""
        url = self._upload_url(sandbox_name)
        logger.info("[CsgHubSandbox] csg-sandbox-upload-file trace=%s", sandbox_name)
        try:
            async with httpx.AsyncClient(trust_env=False, timeout=timeout) as client:
                resp = await client.post(
                    url,
                    headers=self._auth_headers(),
                    files={"file": (file_name, file_bytes)},
                )
                if resp.status_code != 200:
                    detail = _log_error_body(resp.text)
                    logger.error(
                        "[CsgHubSandbox] csg-sandbox-upload-file HTTP error: %s url=%s body=%s",
                        resp.status_code,
                        url.split("?", 1)[0],
                        detail[:2000],
                    )
                    raise SandboxHttpError(
                        f"HTTP {resp.status_code}: {detail}",
                        status_code=resp.status_code,
                        request_url=str(resp.request.url),
                        detail=detail,
                    )
                try:
                    data = resp.json()
                except json.JSONDecodeError as e:
                    raise SandboxResponseParseError(f"upload response is not valid JSON: {e}") from e
                try:
                    return SandboxUploadFileResponse.model_validate(data)
                except ValidationError as e:
                    raise SandboxResponseParseError(str(e), detail=str(e)) from e
        except SandboxHttpError:
            raise
        except SandboxResponseParseError:
            raise
        except httpx.RequestError as e:
            logger.error("[CsgHubSandbox] csg-sandbox-upload-file request failed: %s", e)
            raise _transport_error(e) from e

    async def get_sandbox_runtime_health(
        self,
        sandbox_name: str,
        *,
        timeout: float = _TIMEOUT,
    ) -> None:
        """GET the sandbox-runtime root through the gateway (readiness probe; follows redirects)."""
        await self._raw_request(
            span_name="csg-sandbox-runtime-health",
            method="GET",
            url=self._runtime_health_url(sandbox_name),
            json_body=None,
            success_statuses=(200,),
            timeout=timeout,
            trace_label=sandbox_name,
            follow_redirects=True,
        )

    async def get_sandbox(self, sandbox_id: str) -> SandboxResponse:
        """Return current spec and state for ``GET /api/v1/sandboxes/{sandbox_id}``."""
        resp = await self._raw_request(
            span_name="csg-sandbox-get",
            method="GET",
            url=f"{self._root()}/{sandbox_id}",
            json_body=None,
            success_statuses=(200,),
            timeout=_TIMEOUT,
            trace_label=sandbox_id,
        )
        body = _response_json(resp)
        parsed = _parse_sandbox_response_json(body)
        _log_lifecycle_response(
            span_name="csg-sandbox-get",
            trace_label=sandbox_id,
            response=parsed,
        )
        return parsed

    async def update_sandbox_config(self, sandbox_id: str, body: SandboxUpdateConfigRequest) -> SandboxResponse:
        """Patch mutable fields (image, env, volumes, port, timeout) for an existing sandbox."""
        resp = await self._raw_request(
            span_name="csg-sandbox-update-config",
            method="PATCH",
            url=f"{self._root()}/{sandbox_id}",
            json_body=_dump_update_config_body(body),
            success_statuses=(200,),
            timeout=_TIMEOUT,
            trace_label=sandbox_id,
        )
        parsed = _parse_sandbox_response_json(_response_json(resp))
        _log_lifecycle_response(
            span_name="csg-sandbox-update-config",
            trace_label=sandbox_id,
            response=parsed,
        )
        return parsed

    async def apply_sandbox(self, spec: SandboxCreateRequest) -> SandboxResponse:
        """Declarative update: maps :class:`SandboxCreateRequest` into a PATCH by ``sandbox_name``."""
        update = SandboxUpdateConfigRequest(
            resource_id=spec.resource_id,
            image=spec.image,
            environments=spec.environments,
            volumes=list(spec.volumes),
            port=spec.port,
            timeout=spec.timeout,
        )
        return await self.update_sandbox_config(spec.sandbox_name, update)

    async def start_sandbox(self, sandbox_id: str) -> SandboxResponse:
        """Start workload: ``PUT .../sandboxes/{id}/status/start``."""
        resp = await self._raw_request(
            span_name="csg-sandbox-start",
            method="PUT",
            url=f"{self._root()}/{sandbox_id}/status/start",
            json_body=None,
            success_statuses=(200,),
            timeout=_TIMEOUT,
            trace_label=sandbox_id,
        )
        parsed = _parse_sandbox_response_json(_response_json(resp))
        _log_lifecycle_response(
            span_name="csg-sandbox-start",
            trace_label=sandbox_id,
            response=parsed,
        )
        return parsed

    async def stop_sandbox(self, sandbox_id: str) -> None:
        """Stop workload: ``PUT .../sandboxes/{id}/status/stop`` (primary teardown hook)."""
        await self._raw_request(
            span_name="csg-sandbox-stop",
            method="PUT",
            url=f"{self._root()}/{sandbox_id}/status/stop",
            json_body=None,
            success_statuses=(200,),
            timeout=_TIMEOUT,
            trace_label=sandbox_id,
        )
        logger.info("[CsgHubSandbox] csg-sandbox-stop response trace=%s", sandbox_id)

    async def _raw_request(
        self,
        span_name: str,
        method: str,
        url: str,
        json_body: Optional[Dict[str, Any]],
        success_statuses: tuple[int, ...],
        timeout: float,
        trace_label: str,
        *,
        follow_redirects: bool = False,
    ) -> httpx.Response:
        """Internal JSON request helper: validates status, maps errors to SDK exceptions."""
        logger.info("[CsgHubSandbox] %s trace=%s url=%s", span_name, trace_label, url)
        try:
            async with httpx.AsyncClient(trust_env=False, timeout=timeout) as client:
                resp = await client.request(
                    method,
                    url,
                    headers=self._headers(),
                    json=json_body,
                    follow_redirects=follow_redirects,
                )

                if resp.status_code not in success_statuses:
                    detail = _log_error_body(resp.text)
                    logger.error(
                        "[CsgHubSandbox] %s HTTP %s trace=%s url=%s response_body=%s",
                        span_name,
                        resp.status_code,
                        trace_label,
                        url,
                        detail[:2000],
                    )
                    resp.raise_for_status()

                return resp

        except httpx.HTTPStatusError as e:
            detail = _log_error_body(e.response.text)
            raise SandboxHttpError(
                f"HTTP {e.response.status_code}: {detail}",
                status_code=e.response.status_code,
                request_url=str(e.request.url),
                detail=detail,
            ) from e

        except httpx.RequestError as e:
            logger.error("[CsgHubSandbox] %s request failed: %s", span_name, e)
            raise _transport_error(e) from e


def _response_json(resp: httpx.Response) -> Any:
    """Parse JSON body or raise :class:`~pycsghub.errors.SandboxResponseParseError`."""
    try:
        return resp.json()
    except json.JSONDecodeError as e:
        raise SandboxResponseParseError(f"response body is not valid JSON: {e}") from e
