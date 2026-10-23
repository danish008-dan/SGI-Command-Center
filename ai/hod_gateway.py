# ai/hod_gateway.py
from langchain_openai import ChatOpenAI
from config import GROQ_API_KEY

def get_hod_llm():
    """Returns a lightweight LLM instance configured for Groq."""
    return ChatOpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
        model="openai/gpt-oss-120b",
        temperature=0.2
    )