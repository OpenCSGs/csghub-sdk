"""
CSGHub SDK - A Python SDK for CSGHub
"""

__version__ = "0.7.4"
__author__ = "opencsg"
__email__ = "contact@opencsg.com"

# 导入主要功能
from .file_download import file_download, snapshot_download_parallel, MultiThreadDownloader
from .repository import Repository
from .snapshot_download import snapshot_download

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "file_download",
    "snapshot_download",
    "snapshot_download_parallel",
    "MultiThreadDownloader",
    "Repository"
]
