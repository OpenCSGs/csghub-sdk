import json
import os
import subprocess
import sys
from typing import Dict, List, Optional
import logging
from .constants import LFS_MULTIPART_UPLOAD_COMMAND
from huggingface_hub.utils._lfs import SliceFileObj
import requests

logger = logging.getLogger(__name__)

class LfsEnableCommand:
    def __init__(self, path):
        self.path = path

    def run(self):
        local_path = os.path.abspath(self.path)
        if not os.path.isdir(local_path):
            logger.error("This does not look like a valid git repo.")
            exit(1)
        subprocess.run(
            "git config lfs.customtransfer.multipart.path csghub-cli".split(),
            check=True,
            cwd=local_path,
        )
        subprocess.run(
            f"git config lfs.customtransfer.multipart.args {LFS_MULTIPART_UPLOAD_COMMAND}".split(),
            check=True,
            cwd=local_path,
        )
        logger.info(f"Local repo '{local_path}' set up for largefiles")

def write_msg(msg: Dict):
    """Write out the message in Line delimited JSON."""
    msg_str = json.dumps(msg) + "\n"
    sys.stdout.write(msg_str)
    sys.stdout.flush()


def read_msg() -> Optional[Dict]:
    """Read Line delimited JSON from stdin."""
    msg = json.loads(sys.stdin.readline().strip())

    if "terminate" in (msg.get("type"), msg.get("event")):
        # terminate message received
        return None

    if msg.get("event") not in ("download", "upload"):
        logger.critical("Received unexpected message")
        sys.exit(1)

    return msg

class LfsUploadCommand:

    def run(self) -> None:
        # Immediately after invoking a custom transfer process, git-lfs
        # sends initiation data to the process over stdin.
        # This tells the process useful information about the configuration.
        init_msg = json.loads(sys.stdin.readline().strip())
        if not (init_msg.get("event") == "init" and init_msg.get("operation") == "upload"):
            write_msg({"error": {"code": 32, "message": "Wrong lfs init operation"}})
            sys.exit(1)

        # The transfer process should use the information it needs from the
        # initiation structure, and also perform any one-off setup tasks it
        # needs to do. It should then respond on stdout with a simple empty
        # confirmation structure, as follows:
        write_msg({})

        # After the initiation exchange, git-lfs will send any number of
        # transfer requests to the stdin of the transfer process, in a serial sequence.
        while True:
            msg = read_msg()
            if msg is None:
                # When all transfers have been processed, git-lfs will send
                # a terminate event to the stdin of the transfer process.
                # On receiving this message the transfer process should
                # clean up and terminate. No response is expected.
                sys.exit(0)

            oid = msg["oid"]
            filepath = msg["path"]
            completion_url = msg["action"]["href"]
            header = msg["action"]["header"]
            chunk_size = int(header.pop("chunk_size"))
            presigned_urls: List[str] = list(header.values())

            # Send a "started" progress event to allow other workers to start.
            # Otherwise they're delayed until first "progress" event is reported,
            # i.e. after the first 5GB by default (!)
            write_msg(
                {
                    "event": "progress",
                    "oid": oid,
                    "bytesSoFar": 1,
                    "bytesSinceLast": 0,
                }
            )

            parts = []
            with open(filepath, "rb") as file:
                for i, presigned_url in enumerate(presigned_urls):
                    with SliceFileObj(
                        file,
                        seek_from=i * chunk_size,
                        read_limit=chunk_size,
                    ) as data:
                        r = requests.put(presigned_url, data=data)
                        if r.status_code != 200:
                            logger.error(f"Failed to upload part {i} on {presigned_url} :{r.status_code} {r.text}")
                            
                        r.raise_for_status()
                        parts.append(
                            {
                                "etag": r.headers.get("etag"),
                                "partNumber": i + 1,
                            }
                        )
                        # In order to support progress reporting while data is uploading / downloading,
                        # the transfer process should post messages to stdout
                        write_msg(
                            {
                                "event": "progress",
                                "oid": oid,
                                "bytesSoFar": (i + 1) * chunk_size,
                                "bytesSinceLast": chunk_size,
                            }
                        )
                        # Not precise but that's ok.

            r = requests.post(
                completion_url,
                json={
                    "oid": oid,
                    "parts": parts,
                },
            )
            if r.status_code != 200:
                logger.error(f"Failed to complete multipart on {completion_url} :{r.status_code} {r.text}")

            r.raise_for_status()

            write_msg({"event": "complete", "oid": oid})
