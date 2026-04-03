"""Shared fixtures for sandbox_client tests."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any, Optional

import httpx
import pytest

from pycsghub.sandbox_client.config import CsgHubSandboxConfig

_REAL_ASYNC_CLIENT = httpx.AsyncClient


def run_async(coro: Any) -> Any:
    return asyncio.run(coro)


@pytest.fixture
def csghub_sandbox_cfg_minimal() -> CsgHubSandboxConfig:
    return CsgHubSandboxConfig.model_construct(
        base_url="http://sandbox-api.test",
        aigateway_url="",
    )


def _minimal_state() -> dict[str, Any]:
    return {
        "status": "Running",
        "exited_code": 0,
        "created_at": "2024-01-01T00:00:00Z",
        "started_at": "2024-01-01T00:00:01Z",
    }


def sample_sandbox_response(
    *,
    sandbox_name: str = "sandbox-user-abc",
) -> dict[str, Any]:
    return {
        "spec": {
            "image": "sandbox:test",
            "sandbox_name": sandbox_name,
            "environments": {},
            "volumes": [],
        },
        "state": _minimal_state(),
    }


def sample_runner_create_response(*, sandbox_id: str = "sandbox-user-abc") -> dict[str, Any]:
    return sample_sandbox_response(sandbox_name=sandbox_id)


def sample_httpbase_envelope(msg: str, data: Optional[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {"msg": msg}
    if data is not None:
        out["data"] = data
    return out


def sample_sandbox_get_json(*, sandbox_name: str = "test-sb") -> dict[str, Any]:
    return sample_httpbase_envelope("OK", sample_sandbox_response(sandbox_name=sandbox_name))


def sample_v1_patch_success_json(*, sandbox_id: str = "sb-1") -> dict[str, Any]:
    return sample_httpbase_envelope("OK", sample_sandbox_response(sandbox_name=sandbox_id))


def make_mock_transport(
    handler: Callable[[httpx.Request], httpx.Response],
) -> httpx.MockTransport:
    return httpx.MockTransport(handler)


def patch_async_client_with_transport(
    monkeypatch: pytest.MonkeyPatch,
    transport: httpx.MockTransport,
) -> None:
    def async_client_factory(*args: Any, **kwargs: Any) -> httpx.AsyncClient:
        kwargs["transport"] = transport
        return _REAL_ASYNC_CLIENT(*args, **kwargs)

    monkeypatch.setattr(
        "pycsghub.sandbox_client.client.httpx.AsyncClient",
        async_client_factory,
    )
