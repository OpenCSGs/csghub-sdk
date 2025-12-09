"""Contains commands to print information about the environment and version.

Usage:
    csghub-cli env
    csghub-cli version
"""

import importlib.metadata
import platform
import sys
from typing import Any

from pycsghub import __version__
from pycsghub.utils import disable_xnet, get_default_cache_dir, get_endpoint, get_token_to_send, get_xnet_endpoint

_PY_VERSION: str = sys.version.split()[0].rstrip("+")
_package_versions = {}

_CANDIDATES = {
    "hf_xet"     : {"hf_xet"},
    "hf_version" : {"huggingface_hub"},
    "httpx"      : {"httpx"},
    "aiohttp"    : {"aiohttp"},
    "fastapi"    : {"fastapi"},
    "fastcore"   : {"fastcore"},
    "jinja"      : {"Jinja2"},
    "numpy"      : {"numpy"},
    "pillow"     : {"Pillow"},
    "pydantic"   : {"pydantic"},
    "pydot"      : {"pydot"},
    "safetensors": {"safetensors"},
    "tensorboard": {"tensorboardX"},
    "torch"      : {"torch"},
}

# Check once at runtime
for candidate_name, package_names in _CANDIDATES.items():
    _package_versions[candidate_name] = "N/A"
    for name in package_names:
        try:
            _package_versions[candidate_name] = importlib.metadata.version(name)
            break
        except importlib.metadata.PackageNotFoundError:
            pass

def _get_version(package_name: str) -> str:
    return _package_versions.get(package_name, "N/A")

def env() -> None:
    """Print information about the environment."""
    # Generic machine info
    info: dict[str, Any] = {"csghub_hub version": __version__,
                            "Platform"               : platform.platform(),
                            "Python version"         : _PY_VERSION,
                            "hf_xet"                 : _get_version("hf_xet"),
                            "hf_version"             : _get_version("hf_version"),
                            "httpx"                  : _get_version("httpx"),
                            "ENDPOINT"               : get_endpoint(),
                            "ENDPOINT_HF"            : get_xnet_endpoint(get_endpoint()),
                            "TOKEN"                  : get_token_to_send(),
                            "CSGHUB_DISABLE_XNET"    : disable_xnet(),
                            "CSGHUB_CACHE"       : get_default_cache_dir()}
    
    print("\nCopy-and-paste the text below in your GitHub issue.\n")
    print("\n".join([f"- {prop}: {val}" for prop, val in info.items()]) + "\n")
    return info

def version() -> None:
    """Print CLI version."""
    print(__version__)
