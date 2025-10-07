"""Integration test for CodeAgent with RayboxExecutor"""

import os

import pytest
from smolagents import CodeAgent, LiteLLMModel, WebSearchTool

from agents.smolagents.raybox_executor import RayboxExecutor


@pytest.fixture
def api_url():
    """Get Raybox API URL from environment."""
    return os.getenv("RAYBOX_API_URL", "http://localhost:8000")


@pytest.fixture
def anthropic_api_key():
    """Get Anthropic API key from environment."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")
    return api_key


@pytest.fixture
def model(anthropic_api_key):
    """Create LiteLLM model with Anthropic."""
    return LiteLLMModel(
        model_id="claude-3-5-haiku-20241022",
        api_key=anthropic_api_key,
    )


@pytest.fixture
def agent(model):
    """Create CodeAgent with RayboxExecutor."""
    agent = CodeAgent(
        tools=[WebSearchTool()], model=model, executor_type="local", stream_outputs=True
    )

    # Replace with Raybox executor
    agent.python_executor = RayboxExecutor(additional_imports=[], logger=agent.logger)

    return agent


@pytest.mark.integration
def test_codeagent_with_raybox(agent):
    """Test that CodeAgent can run with RayboxExecutor."""
    result = agent.run("What is 15 * 23?")

    assert result is not None
    assert "345" in str(result)


@pytest.mark.integration
def test_codeagent_with_web_search(agent):
    """Test that CodeAgent can use web search and execute code in Raybox."""
    result = agent.run(
        "How many seconds would it take for a leopard at full speed to run through Pont des Arts?"
    )

    assert result is not None
