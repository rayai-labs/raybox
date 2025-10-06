"""
Raybox Sandbox API
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
import ray
import uuid
import subprocess
import tempfile
import time
import os
from podman import PodmanClient


class SandboxCreateRequest(BaseModel):
    """Request to create a new sandbox."""
    timeout: int = Field(default=300, description="Execution timeout in seconds")
    memory_limit_mb: int = Field(default=512, description="Memory limit in MB")
    cpu_limit: float = Field(default=1.0, description="CPU cores limit")


class CodeExecutionRequest(BaseModel):
    """Request to execute code in a sandbox."""
    code: str = Field(..., description="Python code to execute")


class SandboxInfo(BaseModel):
    """Sandbox information response."""
    sandbox_id: str
    status: str
    created_at: str


class ExecutionResult(BaseModel):
    """Code execution result."""
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None
    results: List[Dict[str, Any]] = Field(default_factory=list)
    execution_time_ms: float = 0.0


# Ray Actor for Sandbox with Podman
@ray.remote
class SandboxActor:
    """Isolated sandbox environment using Podman container."""

    def __init__(self, sandbox_id: str, config: Dict[str, Any]):
        self.sandbox_id = sandbox_id
        self.config = config
        self.status = "initializing"
        self.created_at = datetime.utcnow().isoformat()
        self.container_name = f"raybox-{sandbox_id[:8]}"
        self.installed_packages = set()

        # Use from_env() to auto-detect Podman socket from environment
        # Falls back to default Podman socket locations
        self.podman_client = PodmanClient.from_env()
        self.container = None

        # Start Podman container
        self._start_container()

    def _start_container(self):
        """Start a Podman container for this sandbox."""
        try:
            # Create and start container with Python base image
            self.container = self.podman_client.containers.run(
                "python:3.12-slim",
                command=["sleep", "infinity"],
                name=self.container_name,
                detach=True,
                mem_limit=f"{self.config.get('memory_limit_mb', 512)}m",
                cpu_quota=int(self.config.get('cpu_limit', 1.0) * 100000),
                network_mode="none",  # no network access by default
                remove=False
            )
            self.status = "running"
        except Exception as e:
            self.status = "failed"
            raise RuntimeError(f"Failed to start container: {str(e)}")

    def get_info(self) -> Dict[str, Any]:
        """Get sandbox information."""
        return {
            "sandbox_id": self.sandbox_id,
            "status": self.status,
            "created_at": self.created_at,
            "container_name": self.container_name
        }

    def terminate(self):
        """Terminate the sandbox and remove container."""
        try:
            if self.container:
                self.container.stop()
                self.container.remove()
            self.status = "terminated"
        except Exception as e:
            print(f"Error terminating container: {e}")
            self.status = "terminated"
