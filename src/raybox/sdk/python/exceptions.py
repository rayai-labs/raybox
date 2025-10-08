"""
Raybox Python SDK - Exception definitions
"""


class RayboxError(Exception):
    """Base exception for Raybox SDK errors."""

    pass


class SandboxCreationError(RayboxError):
    """Raised when sandbox creation fails."""

    pass


class SandboxNotFoundError(RayboxError):
    """Raised when a sandbox is not found."""

    pass


class ExecutionError(RayboxError):
    """Raised when code execution fails."""

    pass


class APIError(RayboxError):
    """Raised when an API request fails."""

    pass
