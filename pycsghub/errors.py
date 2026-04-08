from __future__ import annotations

from typing import Optional


class NotSupportError(Exception):
    pass


class NoValidRevisionError(Exception):
    pass


class NotExistError(Exception):
    pass


class RequestError(Exception):
    pass


class GitError(Exception):
    pass


class InvalidParameter(Exception):
    pass


class NotLoginException(Exception):
    pass


class FileIntegrityError(Exception):
    pass


class FileDownloadError(Exception):
    pass


class SandboxError(Exception):
    """Base class for CSGHub sandbox HTTP client errors."""


class SandboxHttpError(SandboxError):
    """HTTP status error from sandbox lifecycle or gateway APIs."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        request_url: str,
        detail: str,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.request_url = request_url
        self.detail = detail


class SandboxTransportError(SandboxError):
    """Network or transport failure (timeouts, connection errors, etc.)."""

    def __init__(self, message: str, *, request_url: Optional[str] = None) -> None:
        super().__init__(message)
        self.request_url = request_url


class SandboxResponseParseError(SandboxError):
    """Failed to parse sandbox API response as expected JSON or models."""

    def __init__(self, message: str, *, detail: Optional[str] = None) -> None:
        super().__init__(message)
        self.detail = detail
