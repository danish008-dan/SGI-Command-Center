# ai/career.py
from openai import OpenAI

from config import GROQ_API_KEY
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")


def generate_career_roadmap(cgpa, skills, interests, domain, salary):
    """Generates a human-readable career roadmap using AI."""

    prompt = f"""
    You are an expert Career Counselor for engineering students. 
    A student has provided the following profile:
    - CGPA: {cgpa}
    - Current Skills: {skills}
    - Interests: {interests}
    - Preferred Domain: {domain}
    - Dream Salary: {salary} LPA

    Based on this profile, generate a comprehensive, structured, and encouraging career roadmap in Markdown format. 
    The output must be easy to read for a non-technical person. 

    Use the following structure:

    ## 🎯 Recommended Career Paths
    (List 3 suitable career roles they can aim for, with a 1-line explanation for each)

    ## 🛠️ Skills Analysis
    **Skills you already have:** (List them)
    **Skills you need to learn:** (List the missing skills crucial for their target domain)

    ## 📚 Learning Roadmap
    **Courses to take:** (Recommend 3-4 specific courses with platforms like Coursera, Udemy)
    **Certifications to pursue:** (Recommend 2 industry-recognized certifications)
    **Project Ideas:** (Suggest 2-3 hands-on project ideas they can build to strengthen their portfolio)

    ## 💼 Interview Preparation
    **Target Companies:** (Suggest 3 companies that fit their profile)
    **HR Questions to prepare:** (List 3 common HR questions)
    **Technical Questions to prepare:** (List 3 domain-specific technical questions)

    ## ✨ Final Advice
    (A brief, encouraging closing note)
    """

    system_message: ChatCompletionSystemMessageParam = {
        "role": "system",
        "content": (
            "You are a helpful career counselor assistant. "
            "Provide structured, easy-to-read Markdown responses."
        ),
    }

    user_message: ChatCompletionUserMessageParam = {
        "role": "user",
        "content": prompt,
    }

    messages: list[
        ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam
        ] = [system_message, user_message]

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            temperature=0.7,
        )

        return response.choices[0].message.content

    except Exception as e:
        print("Groq API Error (Career):", e)
        return None

