"""
Raybox Executor - HTTP Client for Raybox API

This executor connects to Raybox API server via HTTP (no Ray dependency required).
"""

import os

import requests
from smolagents import AgentError
from smolagents.local_python_executor import CodeOutput
from smolagents.remote_executors import RemotePythonExecutor


class RayboxExecutor(RemotePythonExecutor):
    """
    Executes Python code using Raybox sandboxes via HTTP API.

    Args:
        additional_imports (`list[str]`): Additional imports to install.
        logger (`Logger`): Logger to use.
        api_url (`str`, optional): Raybox API URL. Defaults to env var RAYBOX_API_URL or http://localhost:8000
        **kwargs: Additional arguments for sandbox configuration.
    """

    def __init__(self, additional_imports: list[str], logger, api_url: str | None = None, **kwargs):
        super().__init__(additional_imports, logger)

        # Get API URL from parameter, env var, or default
        self.api_url = api_url or os.getenv("RAYBOX_API_URL", "http://localhost:8000")
        self.session = requests.Session()

        # Create sandbox via HTTP API
        config = {
            "memory_limit_mb": kwargs.get("memory_limit_mb", 512),
            "cpu_limit": kwargs.get("cpu_limit", 1.0),
            "timeout": kwargs.get("timeout", 300)
        }

        response = self.session.post(f"{self.api_url}/sandboxes", json=config, timeout=300)
        response.raise_for_status()
        sandbox_data = response.json()

        self.sandbox_id = sandbox_data["sandbox_id"]
        self.logger.log(f"Raybox sandbox created: {self.sandbox_id}", level=31)

        # Install additional packages if needed
        if additional_imports:
            self.installed_packages = self.install_packages(additional_imports)
        else:
            self.installed_packages = []

    def install_packages(self, additional_imports: list[str]) -> list[str]:
        """Install Python packages in the sandbox."""
        if not additional_imports:
            return []

        self.logger.log(f"Installing packages: {additional_imports}", level=31)

        response = self.session.post(
            f"{self.api_url}/sandboxes/{self.sandbox_id}/packages",
            json=additional_imports,
            timeout=300
        )
        response.raise_for_status()
        result = response.json()

        if result.get("success"):
            installed: list[str] = result["installed"]
            self.logger.log(f"Installed packages: {', '.join(installed)}", level=31)
            return installed
        else:
            self.logger.log(f"Failed to install packages: {result.get('error', 'Unknown error')}", level=40)
            return []

    def send_tools(self, tools):
        """Override send_tools to add debugging."""
        self.logger.log(f"Sending {len(tools)} tools to sandbox: {list(tools.keys())}", level=31)
        super().send_tools(tools)

    def run_code_raise_errors(self, code: str) -> CodeOutput:
        """Execute code in the Raybox sandbox via HTTP."""
        # Debug: log what code is being executed
        if "def " in code or "class " in code:
            self.logger.log(f"Executing tool definition code (length: {len(code)})", level=31)

        # Execute code via HTTP API
        response = self.session.post(
            f"{self.api_url}/sandboxes/{self.sandbox_id}/execute",
            json={"code": code},
            timeout=300
        )
        response.raise_for_status()
        result = response.json()

        execution_logs = result["stdout"]

        # Check if this is a final answer
        if result.get("is_final_answer"):
            # This is the final answer - decode it and return
            import base64
            import pickle

            final_answer_data = result.get("final_answer_data", "")
            try:
                # The final answer is base64-encoded pickled data in the exception message
                final_answer = pickle.loads(base64.b64decode(final_answer_data))
                return CodeOutput(output=final_answer, logs=execution_logs, is_final_answer=True)
            except Exception:
                # If we can't decode it, just return the raw data
                return CodeOutput(output=final_answer_data, logs=execution_logs, is_final_answer=True)

        # Handle errors (but not if it's a final answer)
        if result["error"]:
            error_message = (
                f"{execution_logs}\n"
                f"Executing code yielded an error:\n"
                f"{result['error']}"
            )
            raise AgentError(error_message, self.logger)

        # Return successful execution
        return CodeOutput(output=execution_logs or None, logs=execution_logs, is_final_answer=False)

    def cleanup(self):
        """Clean up the Raybox sandbox."""
        try:
            if hasattr(self, "sandbox_id"):
                self.logger.log("Shutting down sandbox...", level=31)
                self.session.delete(f"{self.api_url}/sandboxes/{self.sandbox_id}", timeout=300)
                self.logger.log("Sandbox cleanup completed", level=31)
        except Exception as e:
            self.logger.log(f"Error during cleanup: {e}", level=40)
        finally:
            if hasattr(self, "session"):
                self.session.close()
