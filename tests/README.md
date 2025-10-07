# Raybox Tests

## Running Tests

### Unit Tests (default)
```bash
# Run all unit tests (excludes integration tests)
uv run pytest
```

### Integration Tests
```bash
# Run integration tests (with local server and real LLM)
uv run pytest -m integration
```
