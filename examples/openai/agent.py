from openai import OpenAI
from raybox import Sandbox
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create OpenAI client
client = OpenAI()
system = """
You are a concise Python code generator.
Respond only with valid Python code that solves the user's request.
Do not include explanations, comments, markdown formatting, or code fence.
Always print the result so it can be observed.
"""
prompt = "Generate code to reverse a string 'Hello, World!' in Python"

# Call OpenAI chat completion API
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system},
        {"role": "user", "content": prompt}
    ]
)

# Extract the code from the response
code = response.choices[0].message.content

# Execute code in a Raybox Sandbox
if code:
    with Sandbox() as sandbox:
        result = sandbox.execute(code)
        if result.success:
            print(f"Output:\n{result.stdout}")
        else:
            print(f"Error:\n{result.error}")
