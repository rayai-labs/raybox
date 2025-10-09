# Raybox

Secure sandboxes for AI code execution in the cloud.

Raybox provides AI agents with isolated environments to execute arbitrary code, use I/O, access the internet, and run terminal commands safely.

## Quick Start

### Install

```bash
pip install raybox
```

### Authenticate

```bash
raybox login
```

This will open your browser to authenticate. After logging in, you'll receive an API key which will be saved locally at `~/.raybox/config.json`.

### Use the SDK

```python
from raybox import Sandbox

# Execute code in a secure cloud sandbox
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

**Advanced Configuration:**

```python
# Configure sandbox resources
with Sandbox(
    timeout=300,                       # Execution timeout (seconds)
    memory_limit_mb=512,               # Memory limit (MB)
    cpu_limit=1.0                      # CPU cores limit
) as sandbox:
    result = sandbox.execute("print('Configured sandbox')")

# Use custom API endpoint (for self-hosted deployments)
with Sandbox(api_url="https://your-deployment.com") as sandbox:
    result = sandbox.execute("print('Custom endpoint')")
```

## Self-Hosting (Enterprise)

Want to run Raybox on your own infrastructure? The server code is source-available in `/ee`.

```bash
# Install dependencies
uv sync

# Start the server
uv run raybox-server
```

**Note:** Production self-hosting requires an Enterprise license. Contact [enterprise@raybox.ai](mailto:enterprise@raybox.ai).

## Project Structure

```
raybox/
├── src/raybox/sdk/     # Python SDK (MIT License - Open Source)
├── ee/raybox/api/      # Server code (Proprietary - Source Available)
├── tests/sdk/          # SDK tests (MIT)
├── tests/ee/           # Server tests (Proprietary)
└── examples/           # Usage examples
```

## Development

### Running Tests

```bash
# SDK tests (no server required)
uv run pytest tests/sdk/

# Server tests (Requires Docker)
uv run pytest tests/ee/

# Integration tests
uv run pytest tests/integration/ -m integration
```

### Code Quality

```bash
uv run ruff check .
uv run black .
uv run mypy src tests
```

## Requirements

- Python 3.12+
- **For cloud usage:** Just the SDK (no additional requirements)
- **For self-hosting:** Docker + Ray

## License

This project uses dual licensing:

- **SDK** (`/src/raybox/sdk/`): **MIT License** - Free and open source
- **Server** (`/ee/`): **Proprietary** - Source-available, requires license for production use

See [LICENSE](LICENSE) for SDK terms and [ee/LICENSE](ee/LICENSE) for server terms.

## Get Help

- **Documentation:** https://docs.raybox.ai
- **Sign up:** https://raybox.ai
- **Enterprise:** enterprise@raybox.ai
