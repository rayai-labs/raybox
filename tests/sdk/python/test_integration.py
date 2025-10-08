"""
Integration tests for Raybox Python SDK (requires running API server)

Run these tests with: pytest tests/sdk/test_integration.py
Make sure the Raybox API server is running at http://localhost:8000
"""

import pytest

from raybox.sdk.python import Sandbox
from raybox.sdk.python.exceptions import SandboxCreationError


@pytest.mark.integration
class TestSandboxIntegration:
    """Integration tests with live API server."""

    def test_sandbox_creation_and_cleanup(self):
        """Test sandbox can be created and cleaned up."""
        with Sandbox() as sandbox:
            assert sandbox.sandbox_id is not None
            assert len(sandbox.sandbox_id) > 0

        # After context exit, sandbox should be cleaned up
        assert sandbox.sandbox_id is None

    def test_simple_code_execution(self):
        """Test executing simple code."""
        with Sandbox() as sandbox:
            result = sandbox.execute("print('Hello from integration test!')")

            assert result.success is True
            assert "Hello from integration test!" in result.stdout
            assert result.error is None
            assert result.execution_time_ms > 0

    def test_code_with_calculations(self):
        """Test executing code with calculations."""
        with Sandbox() as sandbox:
            code = """
x = 10
y = 20
result = x + y
print(f"Result: {result}")
"""
            result = sandbox.execute(code)

            assert result.success is True
            assert "Result: 30" in result.stdout
            assert result.error is None

    def test_code_with_error(self):
        """Test executing code that raises an error."""
        with Sandbox() as sandbox:
            result = sandbox.execute("print(undefined_variable)")

            assert result.success is False
            assert result.error is not None
            assert "NameError" in result.error or "undefined_variable" in result.error

    def test_multiple_executions(self):
        """Test multiple code executions in same sandbox."""
        with Sandbox() as sandbox:
            # First execution
            result1 = sandbox.execute("x = 42")
            assert result1.success is True

            # Second execution (should remember x)
            result2 = sandbox.execute("print(f'x = {x}')")
            assert result2.success is True
            assert "x = 42" in result2.stdout

            # Third execution
            result3 = sandbox.execute("print(x * 2)")
            assert result3.success is True
            assert "84" in result3.stdout

    def test_install_and_use_packages(self):
        """Test installing and using packages."""
        with Sandbox() as sandbox:
            # Install numpy
            install_result = sandbox.install_packages(["numpy"])
            assert install_result["success"] is True
            assert "numpy" in install_result["installed"]

            # Use numpy
            code = """
import numpy as np
arr = np.array([1, 2, 3, 4, 5])
print(f"Mean: {arr.mean()}")
"""
            result = sandbox.execute(code)
            assert result.success is True
            assert "Mean: 3.0" in result.stdout

    def test_custom_configuration(self):
        """Test sandbox with custom configuration."""
        with Sandbox(
            timeout=600,
            memory_limit_mb=256,
            cpu_limit=0.5,
        ) as sandbox:
            result = sandbox.execute("print('Custom config')")
            assert result.success is True
            assert "Custom config" in result.stdout

    def test_multiline_output(self):
        """Test code that produces multiple lines of output."""
        with Sandbox() as sandbox:
            code = """
for i in range(5):
    print(f"Line {i}")
"""
            result = sandbox.execute(code)

            assert result.success is True
            assert "Line 0" in result.stdout
            assert "Line 4" in result.stdout

    def test_stderr_output(self):
        """Test code that writes to stderr."""
        with Sandbox() as sandbox:
            code = """
import sys
print("stdout message")
print("stderr message", file=sys.stderr)
"""
            result = sandbox.execute(code)

            assert result.success is True
            assert "stdout message" in result.stdout
            assert "stderr message" in result.stderr

    def test_long_running_code(self):
        """Test code that takes some time to execute."""
        with Sandbox() as sandbox:
            code = """
import time
time.sleep(0.5)
print("Done")
"""
            result = sandbox.execute(code)

            assert result.success is True
            assert "Done" in result.stdout
            assert result.execution_time_ms >= 500

    def test_empty_package_list(self):
        """Test installing empty package list."""
        with Sandbox() as sandbox:
            result = sandbox.install_packages([])
            assert result["success"] is True
            assert result["installed"] == []

    @pytest.mark.skipif(True, reason="Test connection error handling - requires API to be down")
    def test_connection_error(self):
        """Test handling of connection errors (run manually with API down)."""
        with pytest.raises(SandboxCreationError):
            with Sandbox(api_url="http://localhost:9999"):
                pass


@pytest.mark.integration
class TestSandboxConcurrency:
    """Test concurrent sandbox usage."""

    def test_multiple_sandboxes(self):
        """Test creating multiple sandboxes concurrently."""
        with Sandbox() as sandbox1, Sandbox() as sandbox2:
            assert sandbox1.sandbox_id != sandbox2.sandbox_id

            result1 = sandbox1.execute("print('Sandbox 1')")
            result2 = sandbox2.execute("print('Sandbox 2')")

            assert "Sandbox 1" in result1.stdout
            assert "Sandbox 2" in result2.stdout

    def test_isolated_execution_contexts(self):
        """Test that sandboxes are isolated from each other."""
        with Sandbox() as sandbox1, Sandbox() as sandbox2:
            # Set variable in sandbox1
            sandbox1.execute("isolated_var = 'sandbox1'")

            # Try to access it in sandbox2 (should fail)
            result = sandbox2.execute("print(isolated_var)")

            assert result.success is False
            assert result.error is not None and (
                "NameError" in result.error or "not defined" in result.error
            )
