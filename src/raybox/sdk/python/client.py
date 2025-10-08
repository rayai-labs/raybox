"""
Raybox Python SDK - Client implementation
"""

import os
from typing import Any

import requests

from .exceptions import APIError, SandboxCreationError, SandboxNotFoundError
from .types import ExecutionResult


class Sandbox:
    """
    Raybox Sandbox client with context manager support.

    Usage:
        with Sandbox() as sandbox:
            result = sandbox.execute("print('Hello, World!')")
            print(result.stdout)

    Args:
        api_url: Raybox API URL. Defaults to RAYBOX_API_URL env var or http://localhost:8000
        timeout: Execution timeout in seconds
        memory_limit_mb: Memory limit in MB
        cpu_limit: CPU cores limit
    """

    def __init__(
        self,
        api_url: str | None = None,
        timeout: int = 300,
        memory_limit_mb: int = 512,
        cpu_limit: float = 1.0,
    ):
        self.api_url = api_url or os.getenv("RAYBOX_API_URL", "http://localhost:8000")
        self.timeout = timeout
        self.memory_limit_mb = memory_limit_mb
        self.cpu_limit = cpu_limit
        self.sandbox_id: str | None = None
        self.session = requests.Session()

    def __enter__(self) -> "Sandbox":
        """Create a sandbox when entering context."""
        try:
            response = self.session.post(
                f"{self.api_url}/sandboxes",
                json={
                    "timeout": self.timeout,
                    "memory_limit_mb": self.memory_limit_mb,
                    "cpu_limit": self.cpu_limit,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            self.sandbox_id = data["sandbox_id"]
            return self
        except requests.exceptions.RequestException as e:
            raise SandboxCreationError(f"Failed to create sandbox: {str(e)}") from e

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Clean up sandbox when exiting context."""
        if self.sandbox_id:
            try:
                self.session.delete(
                    f"{self.api_url}/sandboxes/{self.sandbox_id}",
                    timeout=30,
                )
            except requests.exceptions.RequestException:
                # Ignore errors during cleanup
                pass
            finally:
                self.sandbox_id = None
                self.session.close()

    def execute(self, code: str) -> ExecutionResult:
        """
        Execute Python code in the sandbox.

        Automatically strips markdown code fences if present.

        Args:
            code: Python code to execute (with or without markdown fences)

        Returns:
            ExecutionResult with stdout, stderr, and error information

        Raises:
            SandboxNotFoundError: If sandbox is not initialized
            APIError: If the API request fails
        """
        if not self.sandbox_id:
            raise SandboxNotFoundError("Sandbox not initialized. Use 'with Sandbox()' pattern.")

        # Strip markdown code fences if present
        code = self._strip_markdown_fences(code)

        try:
            response = self.session.post(
                f"{self.api_url}/sandboxes/{self.sandbox_id}/execute",
                json={"code": code},
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()

            return ExecutionResult(
                stdout=data.get("stdout", ""),
                stderr=data.get("stderr", ""),
                error=data.get("error"),
                results=data.get("results", []),
                execution_time_ms=data.get("execution_time_ms", 0.0),
                is_final_answer=data.get("is_final_answer", False),
                final_answer_data=data.get("final_answer_data"),
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise SandboxNotFoundError(f"Sandbox {self.sandbox_id} not found") from e
            raise APIError(f"API request failed: {str(e)}") from e
        except requests.exceptions.RequestException as e:
            raise APIError(f"API request failed: {str(e)}") from e

    def install_packages(self, packages: list[str]) -> dict[str, Any]:
        """
        Install Python packages in the sandbox.

        Args:
            packages: List of package names to install

        Returns:
            Dictionary with installation result

        Raises:
            SandboxNotFoundError: If sandbox is not initialized
            APIError: If the API request fails
        """
        if not self.sandbox_id:
            raise SandboxNotFoundError("Sandbox not initialized. Use 'with Sandbox()' pattern.")

        if not packages:
            return {"success": True, "installed": []}

        try:
            response = self.session.post(
                f"{self.api_url}/sandboxes/{self.sandbox_id}/packages",
                json=packages,
                timeout=300,
            )
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise SandboxNotFoundError(f"Sandbox {self.sandbox_id} not found") from e
            raise APIError(f"Failed to install packages: {str(e)}") from e
        except requests.exceptions.RequestException as e:
            raise APIError(f"Failed to install packages: {str(e)}") from e

    @staticmethod
    def _strip_markdown_fences(code: str) -> str:
        """
        Strip markdown code fences from code string.

        Handles:
        - ```python ... ```
        - ``` ... ```
        - Code without fences (returned as-is)

        Args:
            code: Code string that may contain markdown fences

        Returns:
            Clean code without markdown fences
        """
        code = code.strip()

        # Check if code starts with markdown fence
        if code.startswith("```"):
            lines = code.split("\n")

            # Remove first line (``` or ```python or ```py, etc.)
            lines = lines[1:]

            # Remove last line if it's just ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            code = "\n".join(lines)

        return code.strip()
