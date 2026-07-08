import os

import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-opus-4-7"

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
