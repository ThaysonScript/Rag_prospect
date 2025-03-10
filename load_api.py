import os
from dotenv import load_dotenv

load_dotenv()

os.environ["GROQ_API_KEY"]
os.environ["LANGSMITH_API_KEY"]
os.environ["LANGSMITH_TRACING"] = "true"