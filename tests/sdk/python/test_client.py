"""
Unit tests for Raybox SDK client (with mocking)
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from raybox.sdk.python.client import Sandbox
from raybox.sdk.python.exceptions import APIError, SandboxCreationError, SandboxNotFoundError


class TestSandboxInit:
    """Test Sandbox initialization."""

    def test_default_initialization(self):
        """Test default initialization values (cloud API)."""
        sandbox = Sandbox()

        assert sandbox.api_url == "https://api.raybox.ai"
        assert sandbox.timeout == 300
        assert sandbox.memory_limit_mb == 512
        assert sandbox.cpu_limit == 1.0
        assert sandbox.sandbox_id is None

    def test_custom_initialization(self):
        """Test custom initialization values."""
        sandbox = Sandbox(
            api_url="http://example.com:9000",
            timeout=600,
            memory_limit_mb=1024,
            cpu_limit=2.0,
        )

        assert sandbox.api_url == "http://example.com:9000"
        assert sandbox.timeout == 600
        assert sandbox.memory_limit_mb == 1024
        assert sandbox.cpu_limit == 2.0

    @patch.dict("os.environ", {"RAYBOX_API_URL": "http://env-url:8000"})
    def test_env_var_initialization(self):
        """Test initialization from environment variable."""
        sandbox = Sandbox()
        assert sandbox.api_url == "http://env-url:8000"


class TestSandboxContextManager:
    """Test Sandbox context manager functionality."""

    @patch("raybox.sdk.python.client.requests.Session")
    def test_enter_creates_sandbox(self, mock_session_class):
        """Test that __enter__ creates a sandbox."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_response = Mock()
        mock_response.json.return_value = {"sandbox_id": "test-sandbox-123"}
        mock_session.post.return_value = mock_response

        sandbox = Sandbox()

        with sandbox as s:
            assert s.sandbox_id == "test-sandbox-123"
            mock_session.post.assert_called_once()
            call_args = mock_session.post.call_args
            assert "/sandboxes" in call_args[0][0]
            assert call_args[1]["json"]["timeout"] == 300
            assert call_args[1]["json"]["memory_limit_mb"] == 512

    @patch("raybox.sdk.python.client.requests.Session")
    def test_enter_handles_api_error(self, mock_session_class):
        """Test that __enter__ handles API errors."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_session.post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        sandbox = Sandbox()

        with pytest.raises(SandboxCreationError) as exc_info:
            with sandbox:
                pass

        assert "Failed to create sandbox" in str(exc_info.value)

    @patch("raybox.sdk.python.client.requests.Session")
    def test_exit_deletes_sandbox(self, mock_session_class):
        """Test that __exit__ deletes the sandbox."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock create response
        mock_create_response = Mock()
        mock_create_response.json.return_value = {"sandbox_id": "test-sandbox-123"}
        mock_session.post.return_value = mock_create_response

        sandbox = Sandbox()

        with sandbox:
            pass

        # Verify delete was called
        mock_session.delete.assert_called_once()
        call_args = mock_session.delete.call_args
        assert "test-sandbox-123" in call_args[0][0]
        mock_session.close.assert_called_once()

    @patch("raybox.sdk.python.client.requests.Session")
    def test_exit_handles_delete_error(self, mock_session_class):
        """Test that __exit__ handles delete errors gracefully."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock create response
        mock_create_response = Mock()
        mock_create_response.json.return_value = {"sandbox_id": "test-sandbox-123"}
        mock_session.post.return_value = mock_create_response

        # Mock delete to raise error
        mock_session.delete.side_effect = requests.exceptions.RequestException("Delete failed")

        sandbox = Sandbox()

        # Should not raise exception
        with sandbox:
            pass

        # Verify close was still called
        mock_session.close.assert_called_once()


class TestSandboxExecute:
    """Test Sandbox execute method."""

    @patch("raybox.sdk.python.client.requests.Session")
    def test_execute_success(self, mock_session_class):
        """Test successful code execution."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock create response
        mock_create_response = Mock()
        mock_create_response.json.return_value = {"sandbox_id": "test-sandbox-123"}

        # Mock execute response
        mock_execute_response = Mock()
        mock_execute_response.json.return_value = {
            "stdout": "Hello, World!\n",
            "stderr": "",
            "error": None,
            "results": [],
            "execution_time_ms": 42.5,
            "is_final_answer": False,
        }

        mock_session.post.side_effect = [mock_create_response, mock_execute_response]

        sandbox = Sandbox()

        with sandbox:
            result = sandbox.execute("print('Hello, World!')")

        assert result.stdout == "Hello, World!\n"
        assert result.stderr == ""
        assert result.error is None
        assert result.success is True
        assert result.execution_time_ms == 42.5

    @patch("raybox.sdk.python.client.requests.Session")
    def test_execute_with_error(self, mock_session_class):
        """Test code execution with error."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock create response
        mock_create_response = Mock()
        mock_create_response.json.return_value = {"sandbox_id": "test-sandbox-123"}

        # Mock execute response with error
        mock_execute_response = Mock()
        mock_execute_response.json.return_value = {
            "stdout": "",
            "stderr": "Traceback...\n",
            "error": "NameError: name 'foo' is not defined",
            "results": [],
            "execution_time_ms": 10.0,
        }

        mock_session.post.side_effect = [mock_create_response, mock_execute_response]

        sandbox = Sandbox()

        with sandbox:
            result = sandbox.execute("print(foo)")

        assert result.success is False
        assert result.error == "NameError: name 'foo' is not defined"

    def test_execute_without_context(self):
        """Test that execute raises error without context manager."""
        sandbox = Sandbox()

        with pytest.raises(SandboxNotFoundError) as exc_info:
            sandbox.execute("print('test')")

        assert "not initialized" in str(exc_info.value)

    @patch("raybox.sdk.python.client.requests.Session")
    def test_execute_sandbox_not_found(self, mock_session_class):
        """Test execute with sandbox not found."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock create response
        mock_create_response = Mock()
        mock_create_response.json.return_value = {"sandbox_id": "test-sandbox-123"}
        mock_session.post.return_value = mock_create_response

        # Manually set sandbox_id and mock 404 error
        sandbox = Sandbox()
        with sandbox:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_session.post.side_effect = requests.exceptions.HTTPError(response=mock_response)

            with pytest.raises(SandboxNotFoundError):
                sandbox.execute("print('test')")


class TestSandboxInstallPackages:
    """Test Sandbox install_packages method."""

    @patch("raybox.sdk.python.client.requests.Session")
    def test_install_packages_success(self, mock_session_class):
        """Test successful package installation."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock create response
        mock_create_response = Mock()
        mock_create_response.json.return_value = {"sandbox_id": "test-sandbox-123"}

        # Mock install response
        mock_install_response = Mock()
        mock_install_response.json.return_value = {
            "success": True,
            "installed": ["numpy", "pandas"],
            "output": "Successfully installed...",
        }

        mock_session.post.side_effect = [mock_create_response, mock_install_response]

        sandbox = Sandbox()

        with sandbox:
            result = sandbox.install_packages(["numpy", "pandas"])

        assert result["success"] is True
        assert len(result["installed"]) == 2
        assert "numpy" in result["installed"]

    @patch("raybox.sdk.python.client.requests.Session")
    def test_install_empty_packages(self, mock_session_class):
        """Test installing empty package list."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock create response
        mock_create_response = Mock()
        mock_create_response.json.return_value = {"sandbox_id": "test-sandbox-123"}
        mock_session.post.return_value = mock_create_response

        sandbox = Sandbox()

        with sandbox:
            result = sandbox.install_packages([])

        assert result["success"] is True
        assert result["installed"] == []

    def test_install_packages_without_context(self):
        """Test that install_packages raises error without context manager."""
        sandbox = Sandbox()

        with pytest.raises(SandboxNotFoundError) as exc_info:
            sandbox.install_packages(["numpy"])

        assert "not initialized" in str(exc_info.value)

    @patch("raybox.sdk.python.client.requests.Session")
    def test_install_packages_api_error(self, mock_session_class):
        """Test install_packages with API error."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock create response
        mock_create_response = Mock()
        mock_create_response.json.return_value = {"sandbox_id": "test-sandbox-123"}
        mock_session.post.return_value = mock_create_response

        # Manually trigger error after context creation
        sandbox = Sandbox()
        with sandbox:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_session.post.side_effect = requests.exceptions.HTTPError(response=mock_response)

            with pytest.raises(APIError) as exc_info:
                sandbox.install_packages(["invalid-package"])

            assert "Failed to install packages" in str(exc_info.value)
