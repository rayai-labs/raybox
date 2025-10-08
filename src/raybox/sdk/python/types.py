"""
Raybox Python SDK - Type definitions
"""

from typing import Any


class ExecutionResult:
    """Result from executing code in a Raybox sandbox."""

    def __init__(
        self,
        stdout: str = "",
        stderr: str = "",
        error: str | None = None,
        results: list[dict[str, Any]] | None = None,
        execution_time_ms: float = 0.0,
        is_final_answer: bool = False,
        final_answer_data: str | None = None,
    ):
        self.stdout = stdout
        self.stderr = stderr
        self.error = error
        self.results = results or []
        self.execution_time_ms = execution_time_ms
        self.is_final_answer = is_final_answer
        self.final_answer_data = final_answer_data

    @property
    def success(self) -> bool:
        """Whether the execution succeeded without errors."""
        return self.error is None

    @property
    def output(self) -> str:
        """Combined output (stdout + stderr)."""
        return self.stdout + self.stderr

    def __repr__(self) -> str:
        return (
            f"ExecutionResult(success={self.success}, "
            f"execution_time_ms={self.execution_time_ms:.2f})"
        )
