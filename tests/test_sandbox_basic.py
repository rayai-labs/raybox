"""
Test basic sandbox creation with Podman
"""

import uuid

import pytest
import ray

from api.sandbox import SandboxActor


@pytest.fixture(scope="module")
def ray_context():
    """Initialize Ray for tests."""
    ray.init(ignore_reinit_error=True)
    yield
    ray.shutdown()


@pytest.fixture(scope="module")
def sandbox_config():
    """Sandbox configuration."""
    return {
        "memory_limit_mb": 512,
        "cpu_limit": 1.0,
        "timeout": 300
    }


@pytest.fixture(scope="module")
def sandbox_actor(ray_context, sandbox_config):
    """Create a sandbox actor for testing (shared across all tests in module)."""
    sandbox_id = str(uuid.uuid4())
    actor = SandboxActor.remote(sandbox_id, sandbox_config)
    yield actor
    # Cleanup
    ray.get(actor.terminate.remote())


def test_sandbox_creation(sandbox_actor):
    """Test that a sandbox can be created."""
    info = ray.get(sandbox_actor.get_info.remote())

    assert info is not None
    assert "sandbox_id" in info
    assert info["status"] == "running"


def test_code_execution(sandbox_actor):
    """Test that code can be executed in the sandbox."""
    test_code = """
print("Hello from Raybox!")
print("2 + 2 =", 2 + 2)
"""

    result = ray.get(sandbox_actor.execute.remote(test_code))

    assert result is not None
    assert "stdout" in result
    assert "Hello from Raybox!" in result["stdout"]
    assert "2 + 2 = 4" in result["stdout"]
    assert result["error"] is None
    assert result["execution_time_ms"] > 0
