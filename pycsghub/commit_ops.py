from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union, List
import base64


@dataclass
class CommitOperationAdd:
    path_in_repo: str
    path_or_fileobj: Union[str, Path, bytes]


@dataclass
class CommitOperationDelete:
    path_in_repo: str


def to_base64_content(path_or_fileobj: Union[str, Path, bytes]) -> str:
    if isinstance(path_or_fileobj, (str, Path)):
        with open(path_or_fileobj, 'rb') as f:
            data = f.read()
    else:
        data = path_or_fileobj
    return base64.b64encode(data).decode('utf-8')


def build_payload(operations: List[Union[CommitOperationAdd, CommitOperationDelete]], commit_message: str) -> dict:
    files = []
    for op in operations:
        if isinstance(op, CommitOperationAdd):
            files.append({
                'path': op.path_in_repo,
                'action': 'create',
                'content': to_base64_content(op.path_or_fileobj),
            })
        else:
            files.append({
                'path': op.path_in_repo,
                'action': 'delete',
            })
    return {
        'message': commit_message,
        'files': files,
    }

