"""Tests for pycsghub.cmd.sandbox helpers (no network)."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from pycsghub.cmd import sandbox as sandbox_cmd
from pycsghub.constants import DEFAULT_CSGHUB_DOMAIN
from pycsghub.sandbox_client.models import SandboxCreateRequest, SandboxResponse


class TestSandboxCliHelpers(unittest.TestCase):
    def test_parse_env_pairs_parses_and_rejects(self) -> None:
        self.assertEqual(
            sandbox_cmd.parse_env_pairs(["A=1", "B=two=2"]),
            {"A": "1", "B": "two=2"},
        )
        with self.assertRaises(ValueError):
            sandbox_cmd.parse_env_pairs(["no-equals"])

    def test_sandbox_config_defaults(self) -> None:
        cfg = sandbox_cmd.sandbox_config(None, None)
        self.assertEqual(cfg.base_url, DEFAULT_CSGHUB_DOMAIN)
        self.assertEqual(cfg.aigateway_url, "")

    def test_load_create_spec_roundtrip(self) -> None:
        spec = SandboxCreateRequest(
            image="img:tag",
            sandbox_name="sn1",
            cluster_id="c1",
            resource_id=1,
            environments={"K": "V"},
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "spec.json"
            path.write_text(spec.model_dump_json(), encoding="utf-8")
            loaded = sandbox_cmd.load_create_spec(str(path))
        self.assertEqual(loaded.sandbox_name, "sn1")
        self.assertEqual(loaded.image, "img:tag")

    def test_create_requires_image_or_spec(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            sandbox_cmd.create(
                token=None,
                endpoint=None,
                aigateway_url=None,
                image=None,
                name=None,
                cluster_id="",
                resource_id=77,
                port=0,
                timeout=0,
                env=None,
                spec_path=None,
            )
        self.assertEqual(ctx.exception.code, 1)


class TestSandboxCliCreateMocked(unittest.TestCase):
    def test_create_calls_client_and_prints_json(self) -> None:
        sample = SandboxResponse.model_validate(
            {
                "spec": {
                    "sandbox_name": "x",
                    "image": "i",
                    "environments": {},
                    "volumes": [],
                    "port": 0,
                },
                "state": {
                    "status": "Running",
                    "exited_code": 0,
                    "created_at": "2020-01-01T00:00:00Z",
                    "timeout": 0,
                },
            },
        )

        with patch("pycsghub.cmd.sandbox.CsgHubSandbox") as mock_cls:
            instance = MagicMock()
            instance.create_sandbox = AsyncMock(return_value=sample)
            mock_cls.return_value = instance
            with patch("builtins.print") as mock_print:
                sandbox_cmd.create(
                    token="t",
                    endpoint="https://hub.example.com",
                    aigateway_url="",
                    image="img:1",
                    name="sb1",
                    cluster_id="",
                    resource_id=77,
                    port=0,
                    timeout=0,
                    env=["E=1"],
                    spec_path=None,
                )
            mock_print.assert_called_once()
            out = mock_print.call_args[0][0]
            data = json.loads(out)
            self.assertEqual(data["spec"]["sandbox_name"], "x")

    def test_run_lifecycle_maps_sdk_error_to_exit(self) -> None:
        from pycsghub.errors import SandboxHttpError

        async def boom() -> None:
            raise SandboxHttpError(
                "fail",
                status_code=400,
                request_url="http://u",
                detail="bad",
            )

        with self.assertRaises(SystemExit) as ctx:
            sandbox_cmd.run_lifecycle(boom())
        self.assertEqual(ctx.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
