"""Tests for sandbox Pydantic models (no mocks).

SDK does not ship ``SandboxPathExistsResponse`` / ``exists`` API (see package docs).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from pycsghub.sandbox_client.models import (
    RunnerVolumeSpec,
    SandboxCreateRequest,
    SandboxCreateResponse,
    SandboxResponse,
    SandboxState,
    SandboxUpdateConfigRequest,
)


class TestSandboxCreateRequest:
    def test_when_json_matches_api_then_fields_round_trip(self) -> None:
        raw = {
            "image": "x:y",
            "resource_id": 42,
            "sandbox_name": "sn-1",
            "environments": {"A": "b"},
            "volumes": [
                {
                    "sandbox_mount_subpath": "sub",
                    "sandbox_mount_path": "/w",
                    "read_only": False,
                },
            ],
        }
        spec = SandboxCreateRequest.model_validate(raw)

        assert spec.resource_id == 42
        assert spec.sandbox_name == "sn-1"
        assert spec.environments == {"A": "b"}
        assert spec.volumes[0].sandbox_mount_subpath == "sub"

    def test_when_resource_id_omitted_then_defaults_to_77(self) -> None:
        raw = {"image": "x:y", "sandbox_name": "sn-2"}
        spec = SandboxCreateRequest.model_validate(raw)
        assert spec.resource_id == 77
        assert spec.port == 0
        data = spec.model_dump(mode="json", exclude_none=True, by_alias=True)
        assert data["resource_id"] == 77
        assert data["sandbox_name"] == "sn-2"
        assert data["port"] == 0

    def test_when_dumped_then_volume_keys_match_sandbox_volume_json(self) -> None:
        spec = SandboxCreateRequest(
            image="x:y",
            resource_id=1,
            sandbox_name="s1",
            volumes=[
                RunnerVolumeSpec(
                    sandbox_mount_subpath="pvc-sub",
                    sandbox_mount_path="/work",
                    read_only=True,
                ),
            ],
        )
        data = spec.model_dump(mode="json", exclude_none=True, by_alias=True)
        assert data["volumes"][0] == {
            "sandbox_mount_subpath": "pvc-sub",
            "sandbox_mount_path": "/work",
            "read_only": True,
        }


class TestSandboxUpdateConfigRequest:
    def test_when_dumped_then_image_is_required(self) -> None:
        req = SandboxUpdateConfigRequest(resource_id=1, image="img:v1", environments={"K": "v"})
        data = req.model_dump(mode="json", exclude_none=True, exclude_defaults=True, by_alias=True)
        assert data == {"resource_id": 1, "image": "img:v1", "environments": {"K": "v"}}

    def test_when_image_missing_then_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            SandboxUpdateConfigRequest.model_validate({"resource_id": 1})


class TestSandboxResponse:
    def test_when_json_matches_types_sandbox_response_then_spec_and_state_parse(self) -> None:
        raw = {
            "spec": {
                "image": "img:latest",
                "sandbox_name": "sb-1",
                "environments": {},
                "volumes": [],
            },
            "state": {
                "status": "Running",
                "exited_code": 0,
                "created_at": "2024-06-01T12:00:00Z",
            },
        }
        resp = SandboxResponse.model_validate(raw)

        assert resp.spec.sandbox_name == "sb-1"
        assert resp.spec.image == "img:latest"
        assert resp.spec.port == 0
        assert resp.state.status == "Running"
        assert resp.state.exited_code == 0


class TestSandboxCreateResponse:
    def test_when_json_matches_then_fields_parse(self) -> None:
        raw = {
            "sandbox_name": "sb-2",
            "image": "img:v2",
            "environments": {"A": "b"},
            "volumes": [],
        }
        spec = SandboxCreateResponse.model_validate(raw)
        assert spec.sandbox_name == "sb-2"
        assert spec.image == "img:v2"
        assert spec.port == 0

    def test_when_spec_includes_port_then_parsed(self) -> None:
        raw = {
            "sandbox_name": "sb-3",
            "image": "img:v3",
            "environments": {},
            "volumes": [],
            "port": 9000,
        }
        spec = SandboxCreateResponse.model_validate(raw)
        assert spec.port == 9000


class TestSandboxState:
    def test_started_at_optional(self) -> None:
        s = SandboxState(
            status="Pending",
            exited_code=-1,
            created_at="2024-01-01T00:00:00Z",
        )
        assert s.started_at is None
