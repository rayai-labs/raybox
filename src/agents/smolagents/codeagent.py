from smolagents import CodeAgent, WebSearchTool
from smolagents import OpenAIServerModel
from dotenv import load_dotenv
import os

load_dotenv()

model = OpenAIServerModel(
    # You can use any model ID available on OpenRouter
    model_id="anthropic/claude-3.5-haiku-20241022",
    # OpenRouter API base URL
    api_base="https://openrouter.ai/api/v1",
    api_key=os.getenv('OPENROUTER_API_KEY'),
)
agent = CodeAgent(tools=[WebSearchTool()], model=model, stream_outputs=True)

agent.run("How many seconds would it take for a leopard at full speed to run through Pont des Arts?")
