"""Use the CSGHub SDK (async) to manage sandboxes: create and query status.

Install: pip install . (from csghub-sdk repo root)
Requires: httpx, pydantic (declared in pyproject.toml).
"""

from __future__ import annotations

import asyncio
import logging

from pycsghub.constants import DEFAULT_CSGHUB_DOMAIN
from pycsghub.sandbox_client import CsgHubSandbox, CsgHubSandboxConfig, SandboxCreateRequest

# token = "your access token"
token = None

# Hub origin for lifecycle APIs (POST/GET /api/v1/sandboxes). Use your self-hosted URL if needed.
endpoint = DEFAULT_CSGHUB_DOMAIN

# Optional: if sandbox runtime (exec/health) uses a different host than ``endpoint``, set it here.
aigateway_url = ""

logging.basicConfig(
    level=getattr(logging, "INFO"),
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler()],
)


async def main() -> None:
    cfg = CsgHubSandboxConfig(
        base_url=endpoint,
        aigateway_url=aigateway_url,
    )
    client = CsgHubSandbox(csghub_sandbox_cfg=cfg, token=token)

    spec = SandboxCreateRequest(
        image="your-runner-image:tag",
        sandbox_name="my-sandbox",
        resource_id=77,
        port=0,
        timeout=0,
        environments={"KEY": "value"},
    )

    created = await client.create_sandbox(spec)
    print("created:", created.spec.sandbox_name, created.state.status)

    sandbox_id = created.spec.sandbox_name
    current = await client.get_sandbox(sandbox_id)
    print("get:", current.spec.image, current.state.status)


if __name__ == "__main__":
    asyncio.run(main())
