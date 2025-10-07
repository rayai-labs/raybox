"""Integration tests for Raybox API endpoints"""

import pytest
import requests
import os

pytestmark = pytest.mark.integration


@pytest.fixture
def api_url():
    """Get API URL from environment."""
    return os.getenv("RAYBOX_API_URL", "http://localhost:8000")


@pytest.fixture
def api_client(api_url):
    """Create requests session for API calls."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    yield session
    session.close()


@pytest.fixture
def sandbox_id(api_client, api_url):
    """Create a sandbox and return its ID."""
    config = {
        "memory_limit_mb": 512,
        "cpu_limit": 1.0,
        "timeout": 300
    }

    response = api_client.post(f"{api_url}/sandboxes", json=config)
    response.raise_for_status()
    data = response.json()

    sandbox_id = data["sandbox_id"]
    yield sandbox_id

    # Cleanup
    try:
        api_client.delete(f"{api_url}/sandboxes/{sandbox_id}")
    except:
        pass


def test_health_check(api_client, api_url):
    """Test health check endpoint."""
    response = api_client.get(f"{api_url}/health")
    response.raise_for_status()

    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "raybox-api"
    assert "version" in data


def test_create_sandbox(api_client, api_url):
    """Test sandbox creation."""
    config = {
        "memory_limit_mb": 512,
        "cpu_limit": 1.0,
        "timeout": 300
    }

    response = api_client.post(f"{api_url}/sandboxes", json=config)
    response.raise_for_status()

    data = response.json()
    assert "sandbox_id" in data
    assert data["status"] == "running"
    assert "created_at" in data

    # Cleanup
    sandbox_id = data["sandbox_id"]
    api_client.delete(f"{api_url}/sandboxes/{sandbox_id}")


def test_execute_code(api_client, api_url, sandbox_id):
    """Test code execution."""
    code = 'x = 42\nprint(f"x = {x}")'

    response = api_client.post(
        f"{api_url}/sandboxes/{sandbox_id}/execute",
        json={"code": code}
    )
    response.raise_for_status()

    data = response.json()
    assert "stdout" in data
    assert "x = 42" in data["stdout"]
    assert data["error"] is None
    assert data["execution_time_ms"] > 0


def test_stateful_execution(api_client, api_url, sandbox_id):
    """Test that variables persist between executions."""
    # Step 1: Define variable x
    code1 = 'x = 42\nprint(f"x = {x}")'
    response1 = api_client.post(
        f"{api_url}/sandboxes/{sandbox_id}/execute",
        json={"code": code1}
    )
    response1.raise_for_status()
    data1 = response1.json()

    assert "x = 42" in data1["stdout"]
    assert data1["error"] is None

    # Step 2: Use variable x (should persist)
    code2 = 'print(f"x is still {x}")\ny = x * 2\nprint(f"y = {y}")'
    response2 = api_client.post(
        f"{api_url}/sandboxes/{sandbox_id}/execute",
        json={"code": code2}
    )
    response2.raise_for_status()
    data2 = response2.json()

    assert "x is still 42" in data2["stdout"]
    assert "y = 84" in data2["stdout"]
    assert data2["error"] is None


def test_install_packages(api_client, api_url, sandbox_id):
    """Test package installation."""
    packages = ["requests", "numpy"]

    response = api_client.post(
        f"{api_url}/sandboxes/{sandbox_id}/packages",
        json=packages
    )
    response.raise_for_status()

    data = response.json()
    assert data["success"] is True
    assert set(data["installed"]) == set(packages)
    assert "execution_time_ms" in data


def test_get_sandbox_info(api_client, api_url, sandbox_id):
    """Test getting sandbox information."""
    response = api_client.get(f"{api_url}/sandboxes/{sandbox_id}")
    response.raise_for_status()

    data = response.json()
    assert data["sandbox_id"] == sandbox_id
    assert data["status"] == "running"
    assert "created_at" in data


def test_delete_sandbox(api_client, api_url):
    """Test sandbox deletion."""
    # Create a sandbox
    config = {
        "memory_limit_mb": 512,
        "cpu_limit": 1.0,
        "timeout": 300
    }

    create_response = api_client.post(f"{api_url}/sandboxes", json=config)
    create_response.raise_for_status()
    sandbox_id = create_response.json()["sandbox_id"]

    # Delete it
    delete_response = api_client.delete(f"{api_url}/sandboxes/{sandbox_id}")
    delete_response.raise_for_status()

    data = delete_response.json()
    assert data["status"] == "deleted"
    assert data["sandbox_id"] == sandbox_id

    # Verify it's gone
    get_response = api_client.get(f"{api_url}/sandboxes/{sandbox_id}")
    assert get_response.status_code == 404


def test_sandbox_not_found(api_client, api_url):
    """Test that 404 is returned for non-existent sandbox."""
    fake_id = "non-existent-sandbox-id"

    response = api_client.get(f"{api_url}/sandboxes/{fake_id}")
    assert response.status_code == 404
