# ai/resume.py
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types.shared_params.response_format_json_object import (
    ResponseFormatJSONObject,
)
from config import GROQ_API_KEY
from pypdf import PdfReader
import json
import re

client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")


def extract_text_from_pdf(file_path):
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text += page_text + " "
        return text.strip()
    except Exception as e:
        print("PDF Extraction Error:", e)
        return ""


IMPORTANT = {
    "react",
    "next",
    "javascript",
    "typescript",
    "node",
    "python",
    "java",
    "sql",
    "mongodb",
    "mysql",
    "docker",
    "aws",
    "devops",
    "testing",
    "automation",
    "git",
    "ci",
    "cd",
    "ml",
    "ai",
    "opencv",
    "langchain",
    "rag",
}

def to_keywords(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9+.# ]", " ", text)
    words = text.split()
    return [w for w in words if len(w) > 2]


def score_ats(resume_text, jd_text):
    resume_words = set(to_keywords(resume_text))
    jd_words = list(set(to_keywords(jd_text)))
    jd_words = [w for w in jd_words if len(w) > 3]

    matched = []
    missing = []
    for w in jd_words:
        if w in resume_words:
            matched.append(w)
        else:
            missing.append(w)

    total = len(jd_words) + len([w for w in jd_words if w in IMPORTANT])
    got = len(matched) + len([w for w in matched if w in IMPORTANT])

    score = round((got / total) * 100) if total > 0 else 100
    score = min(score, 99)

    return {
        "score": score,
        "matched": sorted(list(set(matched)))[:50],
        "missing": sorted(list(set(missing)))[:50]
    }


def analyze_resume(resume_text, jd_text=""):
    if not resume_text: return None

    # Print length to terminal to verify PDF extraction is working!
    print(f"--- AI Resume Analyzer Triggered ---")
    print(f"Resume Text Length: {len(resume_text)} characters")
    print(f"JD Text Length: {len(jd_text) if jd_text else 0} characters")

    if len(jd_text) > 4000:
        jd_text = jd_text[:4000]

    has_jd = bool(jd_text and jd_text.strip())

    ats_result = {"score": 0, "matched": [], "missing": []}
    if has_jd:
        ats_result = score_ats(resume_text, jd_text)

    if has_jd:
        prompt = f"""
        You are an expert ATS Scanner and Technical Recruiter.
        Analyze the following resume against the job description.

        Resume:
        {resume_text}

        Job Description:
        {jd_text}

        STRICT INSTRUCTIONS:
        - DO NOT generate generic advice. Every point must be specific to the text provided.
        - "improvements": Give 3 specific improvements based ONLY on the resume text provided above.
        - "recommended_companies": Give 3 companies that are hiring for this exact JD or profile.
        - "hr_questions": Generate 3 HR questions based on the experience listed in the resume.
        - "tech_questions": Generate 3 Technical questions based on the skills listed in the resume and required by the JD.
        - "ats_score": Estimate a score (0-100) based on how well the resume matches the JD.

        Return ONLY valid JSON in this exact format:
        {{
          "resume_score": 85,
          "ats_score": 90,
          "improvements": ["Improvement 1", "Improvement 2", "Improvement 3"],
          "recommended_companies": ["Company 1", "Company 2", "Company 3"],
          "interview_prep": {{
              "hr_questions": ["HR 1", "HR 2", "HR 3"],
              "tech_questions": ["Tech 1", "Tech 2", "Tech 3"]
          }}
        }}
        """
    else:
        prompt = f"""
        You are an expert ATS Scanner and Technical Recruiter.
        Analyze the following resume for a general tech role.

        Resume:
        {resume_text}

        STRICT INSTRUCTIONS:
        - DO NOT generate generic advice. Every point must be specific to the text provided.
        - "resume_score": Score (0-100) based on formatting, clarity, and impact of THIS resume.
        - "ats_score": Score (0-100) based on ATS parsing rules (no tables, good headings).
        - "matched_skills": List the top 3 skills explicitly found in the resume text.
        - "missing_skills": List 3 skills that a professional with THIS profile should add to stay competitive.
        - "improvements": Give 3 specific improvements based ONLY on the resume text provided.
        - "recommended_companies": Give 3 companies that fit THIS profile.
        - "hr_questions": Generate 3 HR questions based on the experience listed in the resume.
        - "tech_questions": Generate 3 Technical questions based on the skills listed in the resume.

        Return ONLY valid JSON in this exact format:
        {{
          "resume_score": 85,
          "ats_score": 90,
          "matched_skills": ["Skill 1", "Skill 2", "Skill 3"],
          "missing_skills": ["Skill A", "Skill B", "Skill C"],
          "improvements": ["Improvement 1", "Improvement 2", "Improvement 3"],
          "recommended_companies": ["Company 1", "Company 2", "Company 3"],
          "interview_prep": {{
              "hr_questions": ["HR 1", "HR 2", "HR 3"],
              "tech_questions": ["Tech 1", "Tech 2", "Tech 3"]
          }}
        }}
        """

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                ChatCompletionSystemMessageParam(
                    role="system",
                    content="You are an AI assistant that ONLY returns valid JSON."
                ),
                ChatCompletionUserMessageParam(
                    role="user",
                    content=prompt
                ),
            ],
            response_format=ResponseFormatJSONObject(
                type="json_object"
            ),
            temperature=0.7,
        )
        content = response.choices[0].message.content or "{}"
        ai_data = json.loads(content)


        final_matched = ats_result["matched"] if has_jd else ai_data.get("matched_skills", [])
        final_missing = ats_result["missing"] if has_jd else ai_data.get("missing_skills", [])
        final_ats_score = ats_result["score"] if has_jd else ai_data.get("ats_score", 0)

        return {
            "resume_score": ai_data.get("resume_score", 0),
            "ats_score": final_ats_score,
            "matched_skills": final_matched,
            "missing_skills": final_missing,
            "improvements": ai_data.get("improvements", []),
            "recommended_companies": ai_data.get("recommended_companies", []),
            "interview_prep": ai_data.get("interview_prep", {"hr_questions": [], "tech_questions": []})
        }

    except Exception as e:
        print("Groq API Error:", e)
        return None