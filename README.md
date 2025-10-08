# Raybox

Raybox gives AI Agents secure sandboxes (access to a computer) in the cloud to execute artibitrary code, use I/O, access the internet, or use terminal commands.

## Quick Start

### Start the API Server

```bash
# Install dependencies
uv sync --extra dev

# Start the API server
uv run raybox
```

### Use the Python SDK

```python
from raybox import Sandbox

# Execute code in a secure sandbox
with Sandbox() as sandbox:
    result = sandbox.execute("print('Hello from Raybox!')")
    print(result.stdout)  # Output: Hello from Raybox!

# Install packages and run code
with Sandbox() as sandbox:
    sandbox.install_packages(["numpy", "pandas"])
    result = sandbox.execute("""
import numpy as np
print(np.array([1, 2, 3]).mean())
""")
    print(result.stdout)  # Output: 2.0
```

**SDK Configuration:**

```python
# Configure sandbox resources
with Sandbox(
    api_url="http://localhost:8000",  # Raybox API URL
    timeout=300,                       # Execution timeout (seconds)
    memory_limit_mb=512,               # Memory limit (MB)
    cpu_limit=1.0                      # CPU cores limit
) as sandbox:
    result = sandbox.execute("print('Configured sandbox')")
```

## Development

```bash
# Run tests
make test                  # Unit tests
make test-integration      # Integration tests (requires server)

# Code quality
make format               # Format code
make lint                 # Lint and type check
make check                # All checks
```

## Requirements

- Python 3.12+
- Docker (for container isolation)

## License
MIT
