"""Integration test for RayboxExecutor with smolagents"""

import os
from unittest.mock import MagicMock

import pytest
import ray

from examples.codeagent_smolagent import RayboxExecutor


@pytest.fixture(scope="module")
def ray_context():
    """Initialize Ray for tests."""
    ray.init(ignore_reinit_error=True)
    yield
    ray.shutdown()


@pytest.fixture
def smolagents_logger():
    """Create a logger compatible with smolagents."""
    logger = MagicMock()
    logger.log = MagicMock()
    return logger


@pytest.fixture
def api_url():
    """Get Raybox API URL from environment."""
    return os.getenv("RAYBOX_API_URL", "http://localhost:8000")


@pytest.mark.integration
def test_raybox_executor_basic_execution(ray_context, smolagents_logger, api_url):
    """Test RayboxExecutor can execute basic Python code via real Raybox API."""
    # Create executor (this will create a real sandbox via API)
    executor = RayboxExecutor(additional_imports=[], logger=smolagents_logger, api_url=api_url)

    try:
        # Execute simple math code
        result = executor.run_code_raise_errors("x = 10\ny = 20\nprint(x + y)")

        # Verify execution
        assert result is not None
        assert "30" in result.logs
        assert result.is_final_answer is False

    finally:
        # Clean up sandbox
        executor.cleanup()


@pytest.mark.integration
def test_raybox_executor_with_package_installation(ray_context, smolagents_logger, api_url):
    """Test RayboxExecutor can install packages and use them."""
    # Create executor with package installation
    executor = RayboxExecutor(
        additional_imports=["requests"], logger=smolagents_logger, api_url=api_url
    )

    try:
        # Verify package was installed by importing it
        result = executor.run_code_raise_errors(
            "import requests\nprint(f'requests version: {requests.__version__}')"
        )

        # Verify execution
        assert result is not None
        assert "requests version:" in result.logs

    finally:
        # Clean up sandbox
        executor.cleanup()


@pytest.mark.integration
def test_raybox_executor_stateful_execution(ray_context, smolagents_logger, api_url):
    """Test RayboxExecutor maintains state between executions."""
    # Create executor
    executor = RayboxExecutor(additional_imports=[], logger=smolagents_logger, api_url=api_url)

    try:
        # First execution - define a variable
        result1 = executor.run_code_raise_errors("my_var = 42\nprint(f'Set my_var = {my_var}')")
        assert "Set my_var = 42" in result1.logs

        # Second execution - use the variable from previous execution
        result2 = executor.run_code_raise_errors("print(f'my_var is still {my_var}')")
        assert "my_var is still 42" in result2.logs

    finally:
        # Clean up sandbox
        executor.cleanup()


@pytest.mark.integration
def test_raybox_executor_error_handling(ray_context, smolagents_logger, api_url):
    """Test RayboxExecutor properly handles execution errors."""
    from smolagents import AgentError

    # Create executor
    executor = RayboxExecutor(additional_imports=[], logger=smolagents_logger, api_url=api_url)

    try:
        # Execute code with an error
        with pytest.raises(AgentError) as exc_info:
            executor.run_code_raise_errors("print(undefined_variable)")

        # Verify error message contains the NameError
        assert "NameError" in str(exc_info.value) or "undefined_variable" in str(exc_info.value)

    finally:
        # Clean up sandbox
        executor.cleanup()
