"""
Python executor server that maintains state between executions.
This runs inside the sandbox container.
"""

import json
import sys
import traceback
from io import StringIO


def execute_code(code: str, namespace: dict) -> dict:
    """Execute code in a persistent namespace and capture output."""
    stdout_capture = StringIO()
    stderr_capture = StringIO()

    # Redirect stdout/stderr
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = stdout_capture
    sys.stderr = stderr_capture

    result = {"stdout": "", "stderr": "", "error": None, "exit_code": 0, "is_final_answer": False}

    try:
        # Execute in the persistent namespace
        exec(code, namespace)
        result["stdout"] = stdout_capture.getvalue()
        result["stderr"] = stderr_capture.getvalue()
    except Exception as e:
        # Check if this is a FinalAnswerException (special case - not an error!)
        exception_name = e.__class__.__name__
        if "FinalAnswerException" in exception_name:
            # This is the final answer - extract it and mark as success
            result["is_final_answer"] = True
            result["stdout"] = stdout_capture.getvalue()
            result["stderr"] = stderr_capture.getvalue()
            result["final_answer_data"] = str(e)  # The pickled answer
            result["exit_code"] = 0
        else:
            # Real error
            result["error"] = traceback.format_exc()
            result["stderr"] = stderr_capture.getvalue()
            result["exit_code"] = 1
    finally:
        # Restore stdout/stderr
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    return result


def main():
    """Main loop: read code from stdin, execute, write results to stdout."""
    # Persistent namespace for all executions
    namespace = {"__name__": "__main__", "__builtins__": __builtins__}

    while True:
        try:
            # Read length-prefixed message
            line = sys.stdin.readline()
            if not line:
                break

            data = json.loads(line)
            code = data.get("code", "")

            if code == "__EXIT__":
                break

            result = execute_code(code, namespace)

            # Write result as JSON
            print(json.dumps(result), flush=True)

        except Exception:
            error_result = {
                "stdout": "",
                "stderr": "",
                "error": f"Server error: {traceback.format_exc()}",
                "exit_code": 1,
            }
            print(json.dumps(error_result), flush=True)


if __name__ == "__main__":
    main()
