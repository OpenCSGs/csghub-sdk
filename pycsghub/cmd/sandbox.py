"""CLI helpers for CSGHub sandbox: sync wrappers around async :class:`~pycsghub.sandbox_client.client.CsgHubSandbox`."""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Coroutine, Optional, TypeVar

from pydantic import ValidationError

from pycsghub.constants import DEFAULT_CSGHUB_DOMAIN
from pycsghub.errors import SandboxHttpError, SandboxResponseParseError, SandboxTransportError
from pycsghub.sandbox_client.client import CsgHubSandbox
from pycsghub.sandbox_client.config import CsgHubSandboxConfig
from pycsghub.sandbox_client.models import SandboxCreateRequest, SandboxResponse, SandboxUploadFileResponse

logger = logging.getLogger(__name__)

T = TypeVar("T")


def sandbox_config(
    endpoint: Optional[str],
    aigateway_url: Optional[str],
) -> CsgHubSandboxConfig:
    """Build config; ``endpoint`` maps to Hub lifecycle ``base_url``."""
    base = (endpoint or DEFAULT_CSGHUB_DOMAIN).strip()
    gw = (aigateway_url or "").strip()
    return CsgHubSandboxConfig(base_url=base, aigateway_url=gw)


def response_to_json(resp: SandboxResponse) -> str:
    return json.dumps(
        resp.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
        default=str,
    )


def _print_sandbox_error(e: BaseException) -> None:
    logger.error("sandbox command failed: %s", e)
    if isinstance(e, SandboxHttpError):
        print(f"{e}", file=sys.stderr)
        if e.detail:
            print(e.detail, file=sys.stderr)
    elif isinstance(e, SandboxResponseParseError):
        print(str(e), file=sys.stderr)
        if e.detail:
            print(e.detail, file=sys.stderr)
    else:
        print(str(e), file=sys.stderr)


def run_lifecycle(coro: Coroutine[Any, Any, T]) -> T:
    """Run async sandbox call; map SDK errors to stderr + exit 1."""
    try:
        return asyncio.run(coro)
    except (SandboxHttpError, SandboxTransportError, SandboxResponseParseError) as e:
        _print_sandbox_error(e)
        raise SystemExit(1) from e


def parse_env_pairs(env_list: Optional[list[str]]) -> dict[str, str]:
    out: dict[str, str] = {}
    if not env_list:
        return out
    for item in env_list:
        if "=" not in item:
            msg = f"Invalid --env value (expected KEY=VALUE): {item!r}"
            raise ValueError(msg)
        key, val = item.split("=", 1)
        if not key:
            msg = f"Invalid --env value (empty key): {item!r}"
            raise ValueError(msg)
        out[key] = val
    return out


def load_create_spec(path: str) -> SandboxCreateRequest:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    raw = json.loads(text)
    return SandboxCreateRequest.model_validate(raw)


def create(
    *,
    token: Optional[str],
    endpoint: Optional[str],
    aigateway_url: Optional[str],
    image: Optional[str],
    name: Optional[str],
    cluster_id: str,
    resource_id: int,
    port: int,
    timeout: int,
    env: Optional[list[str]],
    spec_path: Optional[str],
) -> None:
    cfg = sandbox_config(endpoint, aigateway_url)
    try:
        if spec_path:
            spec = load_create_spec(spec_path)
        else:
            if not image or not name:
                msg = "Provide --spec PATH to a JSON file, or both --image and --name."
                raise ValueError(msg)
            spec = SandboxCreateRequest(
                image=image,
                sandbox_name=name,
                cluster_id=cluster_id,
                resource_id=resource_id,
                port=port,
                timeout=timeout,
                environments=parse_env_pairs(env),
            )
    except (ValueError, ValidationError, OSError, json.JSONDecodeError, UnicodeError) as e:
        print(str(e), file=sys.stderr)
        raise SystemExit(1) from e

    logger.info("sandbox create sandbox_name=%s", spec.sandbox_name)

    async def _go() -> SandboxResponse:
        client = CsgHubSandbox(csghub_sandbox_cfg=cfg, token=token)
        return await client.create_sandbox(spec)

    resp = run_lifecycle(_go())
    print(response_to_json(resp))


def get_sandbox(
    *,
    sandbox_id: str,
    token: Optional[str],
    endpoint: Optional[str],
    aigateway_url: Optional[str],
) -> None:
    cfg = sandbox_config(endpoint, aigateway_url)
    logger.info("sandbox get sandbox_id=%s", sandbox_id)

    async def _go() -> SandboxResponse:
        client = CsgHubSandbox(csghub_sandbox_cfg=cfg, token=token)
        return await client.get_sandbox(sandbox_id)

    resp = run_lifecycle(_go())
    print(response_to_json(resp))


def start(
    *,
    sandbox_id: str,
    token: Optional[str],
    endpoint: Optional[str],
    aigateway_url: Optional[str],
) -> None:
    cfg = sandbox_config(endpoint, aigateway_url)
    logger.info("sandbox start sandbox_id=%s", sandbox_id)

    async def _go() -> SandboxResponse:
        client = CsgHubSandbox(csghub_sandbox_cfg=cfg, token=token)
        return await client.start_sandbox(sandbox_id)

    resp = run_lifecycle(_go())
    print(response_to_json(resp))


def stop(
    *,
    sandbox_id: str,
    token: Optional[str],
    endpoint: Optional[str],
    aigateway_url: Optional[str],
) -> None:
    cfg = sandbox_config(endpoint, aigateway_url)
    logger.info("sandbox stop sandbox_id=%s", sandbox_id)

    async def _go() -> None:
        client = CsgHubSandbox(csghub_sandbox_cfg=cfg, token=token)
        await client.stop_sandbox(sandbox_id)

    run_lifecycle(_go())
    print(json.dumps({"status": "ok", "sandbox_id": sandbox_id}, indent=2, ensure_ascii=False))


def delete_sandbox(
    *,
    sandbox_id: str,
    token: Optional[str],
    endpoint: Optional[str],
    aigateway_url: Optional[str],
) -> None:
    """Tear down sandbox resources (same HTTP as stop)."""
    cfg = sandbox_config(endpoint, aigateway_url)
    logger.info("sandbox delete sandbox_id=%s", sandbox_id)

    async def _go() -> None:
        client = CsgHubSandbox(csghub_sandbox_cfg=cfg, token=token)
        await client.delete_sandbox(sandbox_id)

    run_lifecycle(_go())
    print(json.dumps({"status": "ok", "sandbox_id": sandbox_id}, indent=2, ensure_ascii=False))


def exec_command(
    *,
    sandbox_name: str,
    command: str,
    token: Optional[str],
    endpoint: Optional[str],
    aigateway_url: Optional[str],
    exec_timeout: float,
) -> None:
    cfg = sandbox_config(endpoint, aigateway_url)
    logger.info("sandbox exec sandbox_name=%s", sandbox_name)

    async def _go() -> bool:
        failed = False
        client = CsgHubSandbox(csghub_sandbox_cfg=cfg, token=token)
        async for line in client.stream_execute_command(
            sandbox_name,
            command,
            timeout=exec_timeout,
        ):
            print(line)
            if line.startswith("ERROR:"):
                failed = True
        return failed

    failed = run_lifecycle(_go())
    if failed:
        raise SystemExit(1)


def upload(
    *,
    sandbox_name: str,
    local_path: str,
    token: Optional[str],
    endpoint: Optional[str],
    aigateway_url: Optional[str],
    timeout: float,
) -> None:
    cfg = sandbox_config(endpoint, aigateway_url)
    path_obj = Path(local_path)
    if not path_obj.exists():
        print(f"No such file: {local_path}", file=sys.stderr)
        raise SystemExit(1)
    if not path_obj.is_file():
        print(f"Local path must be a file: {local_path}", file=sys.stderr)
        raise SystemExit(1)
    try:
        file_bytes = path_obj.read_bytes()
    except OSError as e:
        print(str(e), file=sys.stderr)
        raise SystemExit(1) from e

    logger.info("sandbox upload sandbox_name=%s file=%s", sandbox_name, path_obj.name)

    async def _go() -> SandboxUploadFileResponse:
        client = CsgHubSandbox(csghub_sandbox_cfg=cfg, token=token)
        return await client.upload_file(
            sandbox_name=sandbox_name,
            file_name=path_obj.name,
            file_bytes=file_bytes,
            timeout=timeout,
        )

    resp = run_lifecycle(_go())
    print(
        json.dumps(
            resp.model_dump(mode="json"),
            indent=2,
            ensure_ascii=False,
        ),
    )


def health(
    *,
    sandbox_name: str,
    token: Optional[str],
    endpoint: Optional[str],
    aigateway_url: Optional[str],
) -> None:
    cfg = sandbox_config(endpoint, aigateway_url)
    logger.info("sandbox health sandbox_name=%s", sandbox_name)

    async def _go() -> None:
        client = CsgHubSandbox(csghub_sandbox_cfg=cfg, token=token)
        await client.get_sandbox_runtime_health(sandbox_name)

    run_lifecycle(_go())
    print("ok")
