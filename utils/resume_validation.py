# utils/resume_validation.py
"""Pydantic models for resume_drafts.content_json validation.

The validation is PERMISSIVE: it accepts both legacy v1 shape (auto-migrated
to v2 via the model_validator) and new v2 shape. It rejects only:
  - Structurally malformed JSON (parse error -> caught in router).
  - Payload > 256 KB (caught in router before model parse).
  - Entry counts exceeding documented caps.
  - String fields exceeding their max_length.

See blueprint §3.1 (field inventory), §3.5 (validation summary), §6.1.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
import re


# === Field length / count limits (blueprint §3.1, §3.5) ===
MAX_FULL_NAME = 120
MAX_EMAIL = 254
MAX_PHONE = 20
MAX_URL = 500
MAX_LOCATION = 120
MAX_SUMMARY = 1000
MAX_FIELD_TITLE = 200           # experience title, project title, cert title, degree
MAX_FIELD_ORG = 200             # organization, issuer, institution
MAX_FIELD_AFFILIATION = 300
MAX_FIELD_CATEGORY = 100        # project category
MAX_FIELD_TECH_STACK = 200      # legacy tech_stack
MAX_FIELD_DATE = 50             # experience/cert dates (free-form string)
MAX_FIELD_EDU_DATE = 20         # education dates (year or month-year)
MAX_FIELD_SCORE_VALUE = 20
MAX_FIELD_SCORE_LABEL = 20
MAX_FIELD_CERTIFICATE_ID = 100
MAX_BULLET_TEXT = 500
MAX_SKILL_VALUE = 100
MAX_SKILL_CATEGORY_NAME = 60

MAX_EXPERIENCE_ENTRIES = 30
MAX_PROJECT_ENTRIES = 30
MAX_CERTIFICATION_ENTRIES = 30
MAX_EDUCATION_ENTRIES = 20
MAX_SKILL_CATEGORIES = 30
MAX_SKILLS_PER_CATEGORY = 30
MAX_BULLETS_PER_ENTRY = 50

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
URL_SCHEMES = ("http://", "https://")


class PersonalInfo(BaseModel):
    full_name: str = Field(..., min_length=0, max_length=MAX_FULL_NAME)
    email: str = Field(..., min_length=0, max_length=MAX_EMAIL)
    phone: Optional[str] = Field(None, max_length=MAX_PHONE)
    linkedin: Optional[str] = Field(None, max_length=MAX_URL)
    location: Optional[str] = Field(None, max_length=MAX_LOCATION)
    github: Optional[str] = Field(None, max_length=MAX_URL)
    portfolio: Optional[str] = Field(None, max_length=MAX_URL)

    @field_validator("email")
    @classmethod
    def _validate_email(cls, v):
        if not v:
            return v
        if not EMAIL_REGEX.match(v):
            raise ValueError(f"Invalid email format: {v[:30]}")
        return v

    @field_validator("linkedin", "github", "portfolio")
    @classmethod
    def _validate_url(cls, v):
        if not v:
            return None
        if not v.startswith(URL_SCHEMES):
            raise ValueError(f"URL must start with http:// or https://: {v[:30]}")
        return v


class ExperienceEntry(BaseModel):
    title: str = Field(..., min_length=0, max_length=MAX_FIELD_TITLE)
    organization: Optional[str] = Field(None, max_length=MAX_FIELD_ORG)
    location: Optional[str] = Field(None, max_length=MAX_LOCATION)
    start_date: Optional[str] = Field(None, max_length=MAX_FIELD_DATE)
    end_date: Optional[str] = Field(None, max_length=MAX_FIELD_DATE)
    bullets: List[str] = Field(default_factory=list, max_length=MAX_BULLETS_PER_ENTRY)

    @field_validator("bullets", mode="before")
    @classmethod
    def _coerce_bullets(cls, v):
        # Tolerate a single string (legacy) -> single-element list
        if isinstance(v, str):
            return [v] if v else []
        return v or []

    @field_validator("bullets")
    @classmethod
    def _check_bullet_lengths(cls, v):
        for b in v:
            if not isinstance(b, str):
                raise ValueError(f"Bullet must be a string: {type(b).__name__}")
            if len(b) > MAX_BULLET_TEXT:
                raise ValueError(f"Bullet exceeds {MAX_BULLET_TEXT} chars: {b[:30]}...")
        return v


class ProjectEntry(BaseModel):
    title: str = Field(..., min_length=0, max_length=MAX_FIELD_TITLE)
    category: Optional[str] = Field(None, max_length=MAX_FIELD_CATEGORY)
    tech_stack: Optional[str] = Field(None, max_length=MAX_FIELD_TECH_STACK)
    bullets: List[str] = Field(default_factory=list, max_length=MAX_BULLETS_PER_ENTRY)

    @field_validator("bullets", mode="before")
    @classmethod
    def _coerce_bullets(cls, v):
        if isinstance(v, str):
            return [v] if v else []
        return v or []

    @field_validator("bullets")
    @classmethod
    def _check_bullet_lengths(cls, v):
        for b in v:
            if not isinstance(b, str):
                raise ValueError("Bullet must be a string")
            if len(b) > MAX_BULLET_TEXT:
                raise ValueError(f"Bullet exceeds {MAX_BULLET_TEXT} chars")
        return v


class CertificationEntry(BaseModel):
    title: str = Field(..., min_length=0, max_length=MAX_FIELD_TITLE)
    issuer: Optional[str] = Field(None, max_length=MAX_FIELD_ORG)
    location: Optional[str] = Field(None, max_length=MAX_LOCATION)
    start_date: Optional[str] = Field(None, max_length=MAX_FIELD_DATE)
    end_date: Optional[str] = Field(None, max_length=MAX_FIELD_DATE)
    certificate_id: Optional[str] = Field(None, max_length=MAX_FIELD_CERTIFICATE_ID)
    url: Optional[str] = Field(None, max_length=MAX_URL)

    @field_validator("url")
    @classmethod
    def _validate_url(cls, v):
        if not v:
            return None
        if not v.startswith(URL_SCHEMES):
            raise ValueError(f"URL must start with http:// or https://: {v[:30]}")
        return v


class EducationEntry(BaseModel):
    degree: str = Field(..., min_length=0, max_length=MAX_FIELD_TITLE)
    institution: Optional[str] = Field(None, max_length=MAX_FIELD_ORG)
    affiliation: Optional[str] = Field(None, max_length=MAX_FIELD_AFFILIATION)
    location: Optional[str] = Field(None, max_length=MAX_LOCATION)
    start_date: Optional[str] = Field(None, max_length=MAX_FIELD_EDU_DATE)
    end_date: Optional[str] = Field(None, max_length=MAX_FIELD_EDU_DATE)
    score_label: Optional[str] = Field(None, max_length=MAX_FIELD_SCORE_LABEL)
    score_value: Optional[str] = Field(None, max_length=MAX_FIELD_SCORE_VALUE)


class ResumeDraft(BaseModel):
    """Top-level resume draft model.

    Accepts v1 (legacy) and v2 shapes; v1 is auto-migrated via
    model_validator(mode="before").
    """
    # Allow extra fields for forward-compat (unknown future fields preserved)
    model_config = {"extra": "allow"}

    schema_version: int = 2
    template_id: str = "dnish_latex_a4"
    personal: PersonalInfo
    summary: Optional[str] = Field(None, max_length=MAX_SUMMARY)
    experience: List[ExperienceEntry] = Field(default_factory=list, max_length=MAX_EXPERIENCE_ENTRIES)
    projects: List[ProjectEntry] = Field(default_factory=list, max_length=MAX_PROJECT_ENTRIES)
    technical_skills: Dict[str, Any] = Field(default_factory=dict)
    certifications: List[CertificationEntry] = Field(default_factory=list, max_length=MAX_CERTIFICATION_ENTRIES)
    education: List[EducationEntry] = Field(default_factory=list, max_length=MAX_EDUCATION_ENTRIES)

    @model_validator(mode="before")
    @classmethod
    def _normalize_input(cls, data):
        """If input is v1 shape (or missing schema_version=2), migrate in-memory."""
        if isinstance(data, dict):
            # Lazy import to avoid circular dependency at module load
            from utils.resume_migration import migrate_v1_to_v2
            if data.get("schema_version") != 2:
                return migrate_v1_to_v2(data)
        return data

    @field_validator("technical_skills")
    @classmethod
    def _validate_skills(cls, v):
        if not isinstance(v, dict):
            raise ValueError("technical_skills must be an object")
        # Count categories (excluding _custom)
        custom = v.get("_custom", [])
        standard_count = sum(1 for k in v if k != "_custom")
        total = standard_count + (len(custom) if isinstance(custom, list) else 0)
        if total > MAX_SKILL_CATEGORIES:
            raise ValueError(
                f"Too many skill categories: {total} (max {MAX_SKILL_CATEGORIES})"
            )
        # Validate standard categories (each value is a list of strings)
        for cat, vals in v.items():
            if cat == "_custom":
                continue
            if not isinstance(vals, list):
                raise ValueError(f"Skill category '{cat}' must be a list")
            if len(vals) > MAX_SKILLS_PER_CATEGORY:
                raise ValueError(
                    f"Too many skills in category '{cat}': {len(vals)} "
                    f"(max {MAX_SKILLS_PER_CATEGORY})"
                )
            for s in vals:
                if not isinstance(s, str):
                    raise ValueError(f"Skill value must be a string in '{cat}'")
                if len(s) > MAX_SKILL_VALUE:
                    raise ValueError(f"Skill value exceeds {MAX_SKILL_VALUE} chars in '{cat}'")
        # Validate _custom list
        if isinstance(custom, list):
            for c in custom:
                if not isinstance(c, dict):
                    raise ValueError("_custom entry must be an object")
                if not c.get("name"):
                    raise ValueError("_custom category requires a 'name' field")
                if len(str(c["name"])) > MAX_SKILL_CATEGORY_NAME:
                    raise ValueError(
                        f"_custom category name exceeds {MAX_SKILL_CATEGORY_NAME} chars"
                    )
                vals = c.get("values", [])
                if not isinstance(vals, list):
                    raise ValueError(f"_custom '{c['name']}' values must be a list")
                if len(vals) > MAX_SKILLS_PER_CATEGORY:
                    raise ValueError(
                        f"Too many skills in _custom '{c['name']}': {len(vals)}"
                    )
                for s in vals:
                    if not isinstance(s, str):
                        raise ValueError(
                            f"Skill value must be a string in _custom '{c['name']}'"
                        )
        return v

    @field_validator("summary")
    @classmethod
    def _coerce_summary(cls, v):
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError("summary must be a string")
        if len(v) > MAX_SUMMARY:
            raise ValueError(f"summary exceeds {MAX_SUMMARY} chars")
        return v
