"""
Unit tests for Raybox SDK types
"""

from raybox.sdk.python.types import ExecutionResult


class TestExecutionResult:
    """Test ExecutionResult class."""

    def test_successful_execution(self):
        """Test successful execution result."""
        result = ExecutionResult(
            stdout="Hello, World!\n",
            stderr="",
            error=None,
            execution_time_ms=42.5,
        )

        assert result.success is True
        assert result.stdout == "Hello, World!\n"
        assert result.stderr == ""
        assert result.error is None
        assert result.execution_time_ms == 42.5
        assert result.output == "Hello, World!\n"

    def test_failed_execution(self):
        """Test failed execution result."""
        result = ExecutionResult(
            stdout="",
            stderr="Traceback...\n",
            error="NameError: name 'foo' is not defined",
            execution_time_ms=10.0,
        )

        assert result.success is False
        assert result.stdout == ""
        assert result.stderr == "Traceback...\n"
        assert result.error == "NameError: name 'foo' is not defined"
        assert result.execution_time_ms == 10.0
        assert result.output == "Traceback...\n"

    def test_combined_output(self):
        """Test combined stdout and stderr output."""
        result = ExecutionResult(
            stdout="Normal output\n",
            stderr="Warning message\n",
            error=None,
            execution_time_ms=5.0,
        )

        assert result.success is True
        assert result.output == "Normal output\nWarning message\n"

    def test_with_results_list(self):
        """Test execution result with results list."""
        results_data = [
            {"type": "plot", "data": "base64data"},
            {"type": "table", "data": "csv data"},
        ]

        result = ExecutionResult(
            stdout="Processing complete\n",
            stderr="",
            error=None,
            results=results_data,
            execution_time_ms=100.0,
        )

        assert result.success is True
        assert len(result.results) == 2
        assert result.results[0]["type"] == "plot"
        assert result.results[1]["type"] == "table"

    def test_final_answer(self):
        """Test execution result with final answer."""
        result = ExecutionResult(
            stdout="",
            stderr="",
            error=None,
            is_final_answer=True,
            final_answer_data="encoded_answer_data",
            execution_time_ms=15.0,
        )

        assert result.success is True
        assert result.is_final_answer is True
        assert result.final_answer_data == "encoded_answer_data"

    def test_default_values(self):
        """Test default values for ExecutionResult."""
        result = ExecutionResult()

        assert result.stdout == ""
        assert result.stderr == ""
        assert result.error is None
        assert result.results == []
        assert result.execution_time_ms == 0.0
        assert result.is_final_answer is False
        assert result.final_answer_data is None
        assert result.success is True

    def test_repr(self):
        """Test string representation."""
        result = ExecutionResult(
            stdout="test",
            error=None,
            execution_time_ms=25.5,
        )

        repr_str = repr(result)
        assert "ExecutionResult" in repr_str
        assert "success=True" in repr_str
        assert "25.50" in repr_str
