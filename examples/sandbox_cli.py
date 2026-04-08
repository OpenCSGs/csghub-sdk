"""Use csghub-cli to manage sandboxes (create, get, start, stop, exec, upload, health).

Install the package so the ``csghub-cli`` entry point is available::

    pip install .

If ``csghub-cli`` is not on PATH, use::

    python -m pycsghub.cli sandbox --help

This file documents typical commands. Set RUN_EXAMPLES = True to execute the
sample ``create`` + ``get`` flow via subprocess (requires a valid token and image).
"""

from __future__ import annotations

import os
import subprocess
import sys

# token = "your access token"
token = None

endpoint = "https://hub.opencsg.com"

# Set True to run the subprocess example at the bottom (optional).
RUN_EXAMPLES = False

# ---------------------------------------------------------------------------
# Shell equivalents (run in terminal)
# ---------------------------------------------------------------------------
#
#   export CSGHUB_TOKEN="your access token"
#   export ENDPOINT="https://hub.opencsg.com"
#
# Create (image + name; port 0 means server default)
#
#   csghub-cli sandbox create -i your-runner-image:tag -n my-sandbox \\
#       -e "$ENDPOINT" -k "$CSGHUB_TOKEN"
#
# Full JSON body (volumes, many env vars): put SandboxCreateRequest JSON in spec.json
#
#   csghub-cli sandbox create --spec /path/to/spec.json -e "$ENDPOINT" -k "$CSGHUB_TOKEN"
#
# Query / lifecycle
#
#   csghub-cli sandbox get my-sandbox -e "$ENDPOINT" -k "$CSGHUB_TOKEN"
#   csghub-cli sandbox start my-sandbox -e "$ENDPOINT" -k "$CSGHUB_TOKEN"
#   csghub-cli sandbox stop my-sandbox -e "$ENDPOINT" -k "$CSGHUB_TOKEN"
#
# Runtime (if gateway differs from Hub, add --aigateway-url)
#
#   csghub-cli sandbox exec my-sandbox "echo hello" -e "$ENDPOINT" -k "$CSGHUB_TOKEN"
#   csghub-cli sandbox upload my-sandbox ./local-file.txt -e "$ENDPOINT" -k "$CSGHUB_TOKEN"
#   csghub-cli sandbox health my-sandbox -e "$ENDPOINT" -k "$CSGHUB_TOKEN"
#


def _token_arg() -> list[str]:
    t = token or os.environ.get("CSGHUB_TOKEN")
    if not t:
        return []
    return ["-k", t]


def run_subprocess_example() -> None:
    """Minimal create + get using the same Python process (optional)."""
    base = [
        sys.executable,
        "-m",
        "pycsghub.cli",
        "sandbox",
        "-e",
        endpoint,
    ]
    create = [
        *base,
        "create",
        "-i",
        "your-runner-image:tag",
        "-n",
        "my-sandbox",
        *_token_arg(),
    ]
    get_cmd = [*base, "get", "my-sandbox", *_token_arg()]
    subprocess.run(create, check=True)
    subprocess.run(get_cmd, check=True)


if __name__ == "__main__":
    if RUN_EXAMPLES:
        run_subprocess_example()
    else:
        print(__doc__)
