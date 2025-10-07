import os

from dotenv import load_dotenv
from smolagents import CodeAgent, LiteLLMModel, WebSearchTool

# Import from installed package
from agents.smolagents import RayboxExecutor

# Load environment variables (including CONTAINER_HOST for Podman)
load_dotenv()

# Use LiteLLM which supports Anthropic
model = LiteLLMModel(
    model_id="claude-3-5-haiku-20241022",
    api_key=os.getenv("ANTHROPIC_API_KEY"),
)

# Create agent with local executor first
agent = CodeAgent(tools=[WebSearchTool()], model=model, executor_type="local", stream_outputs=True)

# Replace with Raybox executor
agent.python_executor = RayboxExecutor(additional_imports=[], logger=agent.logger)

agent.run(
    "How many seconds would it take for a leopard at full speed to run through Pont des Arts?"
)
