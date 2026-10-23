# ai/principal.py
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from config import GROQ_API_KEY

client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")


def ask_principal_assistant(question, context):
    """Answers the principal's question based on live college data."""

    prompt = f"""
    You are an advanced AI Data Analyst Assistant for the Principal of a college. 
    You have been provided with LIVE DATABASE RECORDS of the college below.

    --- LIVE DATABASE RECORDS ---
    {context}
    --- END OF RECORDS ---

    Based STRICTLY on the records provided above, answer the Principal's question. 
    Follow these rules:
    1. If the question asks for a list (e.g., "students in CS"), list their names clearly.
    2. If the data is not present in the records, say "This information is not available in the current database."
    3. Be concise, professional, and direct.
    
    principal's Questions: {question}
    """


    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                ChatCompletionSystemMessageParam(
                    role="system",
                     content="You are a helpful data analyst assistant for a college principal.",
                ),
                ChatCompletionUserMessageParam(
                    role="user",
                    content=prompt
                )
            ],
            temperature=0.18  # Low temperature for factual, data-based answers
        )
        return response.choices[0].message.content
    except Exception as e:
        print("Groq API Error (Principal):", e)
        return "I am unable to process your request right now."