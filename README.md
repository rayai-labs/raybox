# Raybox

Raybox gives AI Agents secure sandboxes (access to a computer) in the cloud to execute artibitrary code, use I/O, access the internet, or use terminal commands.

## Quick Start

```bash
# Install dependencies
uv sync --extra dev

# Start the API server
uv run raybox
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
- Podman (for container isolation)

## License
MIT
