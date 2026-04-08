"""Configuration for :class:`~pycsghub.sandbox_client.client.CsgHubSandbox`.

Defaults target the public CSGHub Hub domain from :mod:`pycsghub.constants`. Override ``base_url``
for self-hosted deployments; set ``aigateway_url`` when sandbox *runtime* routes (streaming
execute, upload, health) are exposed on a different host than the EE lifecycle API.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from pycsghub.constants import DEFAULT_CSGHUB_DOMAIN


class CsgHubSandboxConfig(BaseModel):
    """Endpoints for sandbox lifecycle (Starhub EE/SaaS) vs. runtime proxy (AI Gateway).

    * **Lifecycle** — JSON APIs under ``{base_url}/api/v1/sandboxes``.
    * **Runtime** — ``{aigateway_url}/v1/sandboxes/...`` (execute, upload, batch files). If
      ``aigateway_url`` is empty, runtime calls use ``base_url`` (single-host setups).

    Field aliases (``base-url``, ``aigateway-url``) match TOML-style configuration used elsewhere.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    base_url: str = Field(
        default=DEFAULT_CSGHUB_DOMAIN,
        alias="base-url",
        description="Hub / Starhub origin for /api/v1/sandboxes (create, get, patch, start, stop).",
    )
    aigateway_url: str = Field(
        default="",
        alias="aigateway-url",
        description=(
            "Base URL for sandbox-runtime routes proxied as /v1/sandboxes/... "
            "(execute, upload, batch). Empty string means use base_url."
        ),
    )
