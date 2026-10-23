# ai/teacher.py
from openai import OpenAI
from openai.types import ResponseFormatJSONObject
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from config import GROQ_API_KEY
import json

client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")


def generate_question_paper(subject, unit, difficulty, marks):
    """Generates a structured question paper using Llama 3.1."""

    prompt = f"""
    You are an expert university professor. Create a question paper for:
    - Subject: {subject}
    - Unit/Topic: {unit}
    - Difficulty Level: {difficulty}
    - Total Marks: {marks}

    You MUST respond with ONLY a valid JSON object. Do not include markdown formatting.
    Ensure the total marks of the generated questions add up to {marks}.
    The JSON object must have this exact structure:
    {{
        "mcqs": [
            {{"question": "Question text?", "options": ["A", "B", "C", "D"], "answer": "A", "marks": 2}}
        ],
        "theory": [
            {{"question": "Theory question text", "marks": 5}}
        ],
        "viva": [
            {{"question": "Viva question text", "marks": 1}}
        ]
    }}
    """
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                ChatCompletionSystemMessageParam(
                    role="system",
                    content="You are a helpful AI assistant that only outputs valid JSON.",
                ),
                ChatCompletionUserMessageParam(
                    role="user",
                    content=prompt
                )
            ],
            response_format=ResponseFormatJSONObject(type="json_object"),
            temperature=0.7
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print("Groq API Error (QP):", e)
        return None


def generate_assignment(subject, topic):
    """Generates assignment and practical questions using Llama 3.1."""

    prompt = f"""
    You are an expert university professor. Create an assignment for:
    - Subject: {subject}
    - Topic: {topic}

    You MUST respond with ONLY a valid JSON object. Do not include markdown formatting.
    The JSON object must have this exact structure:
    {{
        "assignments": [
            "Assignment question 1",
            "Assignment question 2"
        ],
        "practical": [
            "Practical lab problem 1",
            "Practical lab problem 2"
        ],
        "viva": [
            "Viva question related to the assignment 1",
            "Viva question 2"
        ]
    }}
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                ChatCompletionSystemMessageParam(
                    role="system",
                    content="You are a helpful AI assistant that only outputs valid JSON.",
                ),
                ChatCompletionUserMessageParam(
                    role="user",
                    content=prompt
                )
            ],
            response_format=ResponseFormatJSONObject(type="json_object"),
            temperature=0.7
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print("Groq API Error (Assignment):", e)
        return None