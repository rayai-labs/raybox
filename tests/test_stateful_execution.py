"""Test stateful code execution"""

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


@pytest.fixture
def sandbox_actor(ray_context):
    """Create a sandbox actor for testing."""
    sandbox_id = str(uuid.uuid4())
    config = {"memory_limit_mb": 512, "cpu_limit": 1.0, "timeout": 300}
    actor = SandboxActor.remote(sandbox_id, config)
    yield actor
    # Cleanup
    ray.get(actor.terminate.remote())


def test_variable_persistence(sandbox_actor):
    """Test that variables persist between executions."""
    # Define a variable
    code1 = "x = 42\nprint(f'x = {x}')"
    result1 = ray.get(sandbox_actor.execute.remote(code1))

    assert result1["error"] is None
    assert "x = 42" in result1["stdout"]

    # Use the variable from previous execution
    code2 = "print(f'x is still {x}')\ny = x * 2\nprint(f'y = {y}')"
    result2 = ray.get(sandbox_actor.execute.remote(code2))

    assert result2["error"] is None
    assert "x is still 42" in result2["stdout"]
    assert "y = 84" in result2["stdout"]


def test_function_persistence(sandbox_actor):
    """Test that functions persist between executions."""
    # Define a function
    code1 = """
def greet(name):
    return f"Hello, {name}!"

print(greet("Raybox"))
"""
    result1 = ray.get(sandbox_actor.execute.remote(code1))

    assert result1["error"] is None
    assert "Hello, Raybox!" in result1["stdout"]

    # Call the function from previous execution
    code2 = "print(greet('World'))"
    result2 = ray.get(sandbox_actor.execute.remote(code2))

    assert result2["error"] is None
    assert "Hello, World!" in result2["stdout"]


def test_state_accumulation(sandbox_actor):
    """Test that state accumulates across multiple executions."""
    # Define first variable
    result1 = ray.get(sandbox_actor.execute.remote("a = 10"))
    assert result1["error"] is None

    # Define second variable
    result2 = ray.get(sandbox_actor.execute.remote("b = 20"))
    assert result2["error"] is None

    # Use both variables
    result3 = ray.get(sandbox_actor.execute.remote("print(f'a + b = {a + b}')"))
    assert result3["error"] is None
    assert "a + b = 30" in result3["stdout"]
