from groq import Groq
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment variables. Please create a .env file with your API key.")

client = Groq(api_key=GROQ_API_KEY)

def call_llm(prompt: str, max_tokens: int = 3000) -> str:
    """
    Sends a prompt to Groq (Llama-3 70B) and returns the response.
    This is the single function used by all agents.
    """
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.2  # low = more consistent code output
    )
    return response.choices[0].message.content