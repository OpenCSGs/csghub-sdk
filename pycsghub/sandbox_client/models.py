"""Pydantic models for CSGHub sandbox REST payloads.

Shapes mirror the Go ``types`` package in Starhub (create/update requests, ``SandboxResponse``,
error bodies). Use these models with :class:`~pycsghub.sandbox_client.client.CsgHubSandbox` to
serialize requests and validate responses. Extra JSON keys are ignored where the server may evolve
without a breaking SDK release (``extra="ignore"`` on read models).
"""

from __future__ import annotations

import datetime  # noqa: TC003
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RunnerVolumeSpec(BaseModel):
    """PVC subpath and mount path inside the sandbox workload (Go ``types.SandboxVolume``)."""

    model_config = ConfigDict(extra="forbid")

    sandbox_mount_subpath: str
    sandbox_mount_path: str
    read_only: bool = False


# Public alias matching Starhub / API naming ("SandboxVolume").
SandboxVolume = RunnerVolumeSpec


class SandboxCreateRequest(BaseModel):
    """Request body for ``POST /api/v1/sandboxes`` (Go ``types.SandboxCreateRequest``).

    The server-side UUID field is not part of the JSON wire format (``json:"-"`` in Go).
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    image: str
    cluster_id: str = Field(
        default="",
        description="Kubernetes cluster id; empty when omitted in incoming JSON.",
    )
    resource_id: int = Field(
        default=77,
        description="Resource pool id; defaults to 77 when omitted in JSON.",
    )
    sandbox_name: str
    environments: dict[str, str] = Field(default_factory=dict)
    volumes: list[RunnerVolumeSpec] = Field(default_factory=list)
    port: int = Field(
        default=0,
        description="Service port; 0 means let the server choose a default.",
    )
    timeout: int = Field(default=0)


class SandboxCreateResponse(BaseModel):
    """Spec snapshot embedded in :class:`SandboxResponse` (Go ``types.SandboxCreateResponse``)."""

    model_config = ConfigDict(extra="ignore")

    sandbox_name: str
    image: str
    environments: dict[str, str] = Field(default_factory=dict)
    volumes: list[RunnerVolumeSpec] = Field(default_factory=list)
    port: int = Field(default=0)


class SandboxState(BaseModel):
    """Runtime status for a sandbox (Go ``types.SandboxState``).

    ``exited_code`` defaults to ``0`` when the backend omits it (older responses).
    """

    model_config = ConfigDict(extra="ignore")

    status: str
    exited_code: int = 0
    created_at: datetime.datetime
    started_at: Optional[datetime.datetime] = None
    timeout: int = Field(default=0)


class SandboxUpdateConfigRequest(BaseModel):
    """Request body for ``PATCH /api/v1/sandboxes/{id}`` (Go ``types.SandboxUpdateConfigRequest``).

    Server UUID is not serialized; the client omits default-empty fields to mirror Go ``omitempty``.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    resource_id: int
    image: str
    environments: dict[str, str] = Field(default_factory=dict)
    volumes: list[RunnerVolumeSpec] = Field(default_factory=list)
    port: int = Field(
        default=0,
        description="Service port; 0 means let the server choose a default.",
    )
    timeout: int = Field(
        default=0,
        description="EE sandbox reclaim/idle timeout in seconds (align with SandboxCreateRequest.timeout).",
    )


class SandboxResponse(BaseModel):
    """Envelope returned by lifecycle APIs (Go ``types.SandboxResponse``).

    The nested ``Create`` field is server-internal and not present on the wire (``json:"-"`` in Go).
    """

    model_config = ConfigDict(extra="ignore")

    spec: SandboxCreateResponse
    state: SandboxState


class SandboxErrorResponse(BaseModel):
    """Error JSON from Starhub or gateways (union of ``message``, ``msg``, ``error`` shapes)."""

    model_config = ConfigDict(extra="ignore")

    code: Optional[int] = None
    message: Optional[str] = None
    error: Optional[str] = None
    msg: Optional[str] = None

    def log_line(self) -> str:
        """Human-readable single line for logs (prefers ``error``, then ``message`` / ``msg``)."""
        if self.error:
            return self.error
        if self.message:
            if self.code is not None:
                return f"{self.code}: {self.message}"
            return self.message
        if self.msg:
            if self.code is not None:
                return f"{self.code}: {self.msg}"
            return self.msg
        return "unknown error"


class SandboxUploadFileResponse(BaseModel):
    """JSON body from ``POST .../v1/sandboxes/{name}/upload`` (multipart upload via gateway)."""

    model_config = ConfigDict(extra="forbid")

    message: str
