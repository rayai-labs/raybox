"""
Raybox Sandbox API
"""

import json
import os
import subprocess
import time
from datetime import datetime
from typing import Any

import ray
from podman import PodmanClient
from pydantic import BaseModel, Field


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
    error: str | None = None
    results: list[dict[str, Any]] = Field(default_factory=list)
    execution_time_ms: float = 0.0


# Ray Actor for Sandbox with Podman
@ray.remote
class SandboxActor:
    """Isolated sandbox environment using Podman container."""

    def __init__(self, sandbox_id: str, config: dict[str, Any]):
        self.sandbox_id = sandbox_id
        self.config = config
        self.status = "initializing"
        self.created_at = datetime.utcnow().isoformat()
        self.container_name = f"raybox-{sandbox_id[:8]}"
        self.installed_packages: set[str] = set()

        # Set CONTAINER_HOST for Podman if not already set
        # This ensures Ray workers can connect to Podman
        if not os.environ.get("CONTAINER_HOST"):
            # Try common Podman socket locations
            podman_sockets = [
                os.path.expanduser("~/.local/share/containers/podman/machine/podman.sock"),
                f"/run/user/{os.getuid()}/podman/podman.sock",
            ]
            for podman_sock in podman_sockets:
                if os.path.exists(podman_sock):
                    os.environ["CONTAINER_HOST"] = f"unix://{podman_sock}"
                    break

        # Use from_env() to auto-detect Podman socket from environment
        # Falls back to default Podman socket locations
        self.podman_client = PodmanClient.from_env()
        self.container: Any = None  # podman.domain.containers.Container type
        self.executor_process: Any = None  # subprocess.Popen type

        # Start Podman container
        self._start_container()

        # Start the executor server inside container
        self._start_executor_server()

    def _start_container(self):
        """Start a Podman container for this sandbox."""
        try:
            # Create and start container with Python base image
            # Using full python image (not slim) to ensure pip is available
            self.container = self.podman_client.containers.run(
                "python:3.12",
                command=["sleep", "infinity"],
                name=self.container_name,
                detach=True,
                mem_limit=f"{self.config.get('memory_limit_mb', 512)}m",
                cpu_quota=int(self.config.get("cpu_limit", 1.0) * 100000),
                network_mode="bridge",  # allow network for package installation
                remove=False,
            )
            self.status = "running"
        except Exception as e:
            self.status = "failed"
            raise RuntimeError(f"Failed to start container: {str(e)}") from e

    def _start_executor_server(self):
        """Start the persistent Python executor server inside the container."""
        # Copy executor server script to container
        executor_script = os.path.join(os.path.dirname(__file__), "executor_server.py")

        with open(executor_script) as f:
            script_content = f.read()

        # Write script to container using exec
        write_cmd = (
            f"cat > /tmp/executor_server.py << 'EXECUTOR_EOF'\n{script_content}\nEXECUTOR_EOF"
        )
        self.container.exec_run(cmd=["sh", "-c", write_cmd])

        # Start the executor server in background using subprocess with podman exec
        # Use full path to podman binary
        podman_bin = "/opt/podman/bin/podman"
        if not os.path.exists(podman_bin):
            # Fallback to system podman
            podman_bin = "podman"

        self.executor_process = subprocess.Popen(
            [podman_bin, "exec", "-i", self.container_name, "python", "/tmp/executor_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

    def execute(self, code: str) -> dict[str, Any]:
        """Execute Python code in the sandbox container using persistent executor."""
        start_time = time.time()

        try:
            # Send code to executor server
            request = json.dumps({"code": code}) + "\n"
            self.executor_process.stdin.write(request)
            self.executor_process.stdin.flush()

            # Read response
            response_line = self.executor_process.stdout.readline()
            result = json.loads(response_line)

            execution_time = (time.time() - start_time) * 1000

            return {
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
                "error": result.get("error"),
                "is_final_answer": result.get("is_final_answer", False),
                "final_answer_data": result.get("final_answer_data"),
                "results": [],
                "execution_time_ms": execution_time,
            }

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return {
                "stdout": "",
                "stderr": str(e),
                "error": str(e),
                "is_final_answer": False,
                "results": [],
                "execution_time_ms": execution_time,
            }

    def install_packages(self, packages: list[str]) -> dict[str, Any]:
        """Install Python packages in the sandbox container."""
        if not packages:
            return {"success": True, "installed": []}

        start_time = time.time()

        try:
            # Install packages using pip
            exit_code, output = self.container.exec_run(
                cmd=["pip", "install", "--root-user-action=ignore"] + packages
            )
            output_str = (
                output.decode("utf-8", errors="replace")
                if isinstance(output, bytes)
                else str(output)
            )
            execution_time = (time.time() - start_time) * 1000

            if exit_code == 0:
                # Track installed packages
                self.installed_packages.update(packages)
                return {
                    "success": True,
                    "installed": packages,
                    "output": output_str,
                    "execution_time_ms": execution_time,
                }
            else:
                return {"success": False, "error": output_str, "execution_time_ms": execution_time}

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return {"success": False, "error": str(e), "execution_time_ms": execution_time}

    def get_info(self) -> dict[str, Any]:
        """Get sandbox information."""
        return {
            "sandbox_id": self.sandbox_id,
            "status": self.status,
            "created_at": self.created_at,
            "container_name": self.container_name,
        }

    def terminate(self):
        """Terminate the sandbox and remove container."""
        try:
            # Stop executor process
            if self.executor_process:
                try:
                    self.executor_process.stdin.write(json.dumps({"code": "__EXIT__"}) + "\n")
                    self.executor_process.stdin.flush()
                    self.executor_process.wait(timeout=2)
                except Exception:
                    self.executor_process.kill()

            # Stop and remove container
            if self.container:
                self.container.stop()
                self.container.remove()

            self.status = "terminated"
        except Exception as e:
            print(f"Error terminating container: {e}")
            self.status = "terminated"
