from smolagents.remote_executors import RemotePythonExecutor
from smolagents.local_python_executor import CodeOutput
from smolagents import AgentError
import ray
import uuid
from api import SandboxActor


class RayboxExecutor(RemotePythonExecutor):
    """
    Executes Python code using Raybox sandboxes.

    Args:
        additional_imports (`list[str]`): Additional imports to install.
        logger (`Logger`): Logger to use.
        **kwargs: Additional arguments for sandbox configuration.
    """

    def __init__(self, additional_imports: list[str], logger, **kwargs):
        super().__init__(additional_imports, logger)

        # Initialize Ray if not already initialized
        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True)

        # Create sandbox configuration
        sandbox_id = str(uuid.uuid4())
        config = {
            "memory_limit_mb": kwargs.get("memory_limit_mb", 512),
            "cpu_limit": kwargs.get("cpu_limit", 1.0),
            "timeout": kwargs.get("timeout", 300)
        }

        # Create Ray sandbox actor
        self.sandbox_actor = SandboxActor.remote(sandbox_id, config)

        # Install additional packages if needed
        if additional_imports:
            self.installed_packages = self.install_packages(additional_imports)
        else:
            self.installed_packages = []

        self.logger.log("Raybox sandbox is running", level=31)  # INFO level

    def install_packages(self, additional_imports: list[str]) -> list[str]:
        """Install Python packages in the sandbox."""
        if not additional_imports:
            return []

        self.logger.log(f"Installing packages: {additional_imports}", level=31)
        result = ray.get(self.sandbox_actor.install_packages.remote(additional_imports))

        if result["success"]:
            self.logger.log(f"Installed packages: {', '.join(result['installed'])}", level=31)
            return result["installed"]
        else:
            self.logger.log(f"Failed to install packages: {result.get('error', 'Unknown error')}", level=40)
            return []

    def send_tools(self, tools):
        """Override send_tools to add debugging."""
        self.logger.log(f"Sending {len(tools)} tools to sandbox: {list(tools.keys())}", level=31)
        super().send_tools(tools)

    def run_code_raise_errors(self, code: str) -> CodeOutput:
        """Execute code in the Raybox sandbox."""
        # Debug: log what code is being executed
        if "def " in code or "class " in code:
            self.logger.log(f"Executing tool definition code (length: {len(code)})", level=31)

        result = ray.get(self.sandbox_actor.execute.remote(code))

        execution_logs = result["stdout"]

        # Check if this is a final answer
        if result.get("is_final_answer"):
            # This is the final answer - decode it and return
            import pickle
            import base64

            final_answer_data = result.get("final_answer_data", "")
            try:
                # The final answer is base64-encoded pickled data in the exception message
                final_answer = pickle.loads(base64.b64decode(final_answer_data))
                return CodeOutput(output=final_answer, logs=execution_logs, is_final_answer=True)
            except:
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
        """Clean up the Raybox sandbox and resources."""
        try:
            if hasattr(self, "sandbox_actor"):
                self.logger.log("Shutting down sandbox...", level=31)  # INFO level
                ray.get(self.sandbox_actor.terminate.remote())
                self.logger.log("Sandbox cleanup completed", level=31)  # INFO level
                del self.sandbox_actor
        except Exception as e:
            self.logger.log(f"Error during cleanup: {e}", level=40)  # ERROR level
