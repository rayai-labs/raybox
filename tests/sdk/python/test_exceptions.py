"""
Unit tests for Raybox SDK exceptions
"""

import pytest

from raybox.sdk.python.exceptions import (
    APIError,
    ExecutionError,
    RayboxError,
    SandboxCreationError,
    SandboxNotFoundError,
)


class TestExceptions:
    """Test SDK exception hierarchy."""

    def test_raybox_error_base(self):
        """Test RayboxError is the base exception."""
        error = RayboxError("Base error")
        assert str(error) == "Base error"
        assert isinstance(error, Exception)

    def test_sandbox_creation_error(self):
        """Test SandboxCreationError."""
        error = SandboxCreationError("Failed to create sandbox")
        assert str(error) == "Failed to create sandbox"
        assert isinstance(error, RayboxError)
        assert isinstance(error, Exception)

    def test_sandbox_not_found_error(self):
        """Test SandboxNotFoundError."""
        error = SandboxNotFoundError("Sandbox abc123 not found")
        assert str(error) == "Sandbox abc123 not found"
        assert isinstance(error, RayboxError)

    def test_execution_error(self):
        """Test ExecutionError."""
        error = ExecutionError("Code execution failed")
        assert str(error) == "Code execution failed"
        assert isinstance(error, RayboxError)

    def test_api_error(self):
        """Test APIError."""
        error = APIError("API request failed: 500 Internal Server Error")
        assert "API request failed" in str(error)
        assert isinstance(error, RayboxError)

    def test_exception_inheritance(self):
        """Test that all SDK exceptions inherit from RayboxError."""
        exceptions = [
            SandboxCreationError("test"),
            SandboxNotFoundError("test"),
            ExecutionError("test"),
            APIError("test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, RayboxError)
            assert isinstance(exc, Exception)

    def test_exception_raising(self):
        """Test that exceptions can be raised and caught."""
        with pytest.raises(SandboxCreationError) as exc_info:
            raise SandboxCreationError("Test creation error")

        assert "Test creation error" in str(exc_info.value)

        # Test catching as RayboxError
        with pytest.raises(RayboxError):
            raise SandboxNotFoundError("Test not found")

    def test_exception_chaining(self):
        """Test exception chaining with 'from' clause."""
        original_error = ValueError("Original error")

        with pytest.raises(APIError) as exc_info:
            try:
                raise original_error
            except ValueError as e:
                raise APIError("Wrapped error") from e

        assert exc_info.value.__cause__ == original_error
