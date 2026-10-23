# utils/resume_migration.py
"""In-memory migration of resume_drafts.content_json from v1 shape to v2 shape.

The migration is:
  - Idempotent: running on already-v2 input returns it unchanged.
  - Lossless: every legacy field is preserved (sometimes under a different key).
  - No DB writes: the migrated shape lives only in the API response. The
    stored draft is untouched; only an explicit Save by the student
    persists the new shape.

v1 shape (legacy):
  {
    "full_name", "email", "phone", "location", "linkedin",
    "summary",
    "skills": [<flat string array>],
    "education": [{"degree", "institution", "start_date", "end_date", "cgpa"}],
    "experience": [{"role", "company", "start_date", "end_date", "description"}],
    "projects": [{"title", "description", "tech_stack"}]
  }

v2 shape (target):
  {
    "schema_version": 2,
    "template_id": "dnish_latex_a4",
    "personal": {"full_name", "email", "phone", "linkedin", "location",
                 "github", "portfolio"},
    "summary",
    "experience": [{"title", "organization", "location",
                     "start_date", "end_date", "bullets": [<string>]}],
    "projects": [{"title", "category", "tech_stack", "bullets": [<string>]}],
    "technical_skills": {<category_name>: [<string>], "_custom": [...]},
    "certifications": [{"title", "issuer", "location", "start_date",
                        "end_date", "certificate_id", "url"}],
    "education": [{"degree", "institution", "affiliation", "location",
                   "start_date", "end_date", "score_label", "score_value"}]
  }
"""

DEFAULT_TEMPLATE_ID = "dnish_latex_a4"


def is_v1(data):
    """Detect whether a parsed dict is in legacy v1 shape."""
    if not isinstance(data, dict):
        return False
    if data.get("schema_version") == 2:
        return False
    # v1 has top-level fields like full_name or skills (flat)
    return (
        "full_name" in data
        or "skills" in data
        or any("role" in e for e in (data.get("experience") or []))
        or any("tech_stack" in p for p in (data.get("projects") or []))
        or any("cgpa" in e for e in (data.get("education") or []))
    )


def migrate_v1_to_v2(data):
    """Upgrade v1 shape to v2 in-memory. Idempotent on v2 input.

    Args:
        data: parsed content_json dict (v1, v2, or partial/malformed).

    Returns:
        A valid v2 dict. If input is not a dict or is malformed, returns a
        minimal valid v2 skeleton with empty fields. Never raises.
    """
    # Guard: non-dict input
    if not isinstance(data, dict):
        return _empty_v2()

    # Idempotent: already v2
    if data.get("schema_version") == 2:
        # Defensive: ensure required top-level keys exist
        return _normalize_v2(data)

    # Malformed: has schema_version but not 2 (e.g., 1, "1", 3, null)
    # Treat as v1 if it has v1 fields; otherwise empty v2.
    if not is_v1(data):
        return _empty_v2()

    # === v1 -> v2 field mapping (lossless) ===
    personal = {
        "full_name": _str_or_empty(data.get("full_name")),
        "email": _str_or_empty(data.get("email")),
        "phone": _str_or_empty(data.get("phone")),
        "linkedin": _str_or_empty(data.get("linkedin")),
        "location": _str_or_empty(data.get("location")),
        "github": data.get("github"),  # not in v1; preserved if somehow present
        "portfolio": data.get("portfolio"),
    }

    summary = _str_or_empty(data.get("summary"))

    # Experience: role -> title, company -> organization, description -> [description]
    experience = []
    for e in (data.get("experience") or []):
        if not isinstance(e, dict):
            continue
        bullets = []
        if e.get("description"):
            bullets = [_str_or_empty(e["description"])]
        experience.append({
            "title": _str_or_empty(e.get("role")),
            "organization": _str_or_empty(e.get("company")),
            "location": e.get("location"),
            "start_date": _str_or_empty(e.get("start_date")),
            "end_date": _str_or_empty(e.get("end_date")),
            "bullets": bullets,
        })

    # Projects: description -> [description], tech_stack preserved + used as category
    projects = []
    for p in (data.get("projects") or []):
        if not isinstance(p, dict):
            continue
        bullets = []
        if p.get("description"):
            bullets = [_str_or_empty(p["description"])]
        tech = _str_or_empty(p.get("tech_stack"))
        projects.append({
            "title": _str_or_empty(p.get("title")),
            # category falls back to tech_stack for legacy data
            "category": _str_or_empty(p.get("category")) or tech or None,
            "tech_stack": tech or None,
            "bullets": bullets,
        })

    # Technical skills: flat array -> {"Other": [...]}
    raw_skills = data.get("skills")
    if isinstance(raw_skills, list) and raw_skills:
        technical_skills = {"Other": [_str_or_empty(s) for s in raw_skills if s]}
    elif isinstance(raw_skills, str) and raw_skills.strip():
        # Defensive: skills as a single string (split on comma)
        technical_skills = {"Other": [s.strip() for s in raw_skills.split(",") if s.strip()]}
    else:
        technical_skills = {}
    technical_skills["_custom"] = []

    # Certifications: not in v1; default to empty array (preserve if present)
    certifications = []
    if isinstance(data.get("certifications"), list):
        for c in data["certifications"]:
            if isinstance(c, dict):
                certifications.append({
                    "title": _str_or_empty(c.get("title")),
                    "issuer": _str_or_empty(c.get("issuer")),
                    "location": c.get("location"),
                    "start_date": _str_or_empty(c.get("start_date")),
                    "end_date": _str_or_empty(c.get("end_date")),
                    "certificate_id": c.get("certificate_id"),
                    "url": c.get("url"),
                })

    # Education: cgpa -> score_label="CGPA", score_value=<cgpa>
    education = []
    for e in (data.get("education") or []):
        if not isinstance(e, dict):
            continue
        cgpa = e.get("cgpa")
        score_label = "CGPA" if cgpa not in (None, "",) else None
        score_value = str(cgpa) if cgpa not in (None, "") else None
        education.append({
            "degree": _str_or_empty(e.get("degree")),
            "institution": _str_or_empty(e.get("institution")),
            "affiliation": e.get("affiliation"),
            "location": e.get("location"),
            "start_date": _str_or_empty(e.get("start_date")),
            "end_date": _str_or_empty(e.get("end_date")),
            "score_label": score_label,
            "score_value": score_value,
        })

    return {
        "schema_version": 2,
        "template_id": data.get("template_id") or DEFAULT_TEMPLATE_ID,
        "personal": personal,
        "summary": summary,
        "experience": experience,
        "projects": projects,
        "technical_skills": technical_skills,
        "certifications": certifications,
        "education": education,
    }


def _normalize_v2(data):
    """Ensure a v2 dict has all required top-level keys (defensive)."""
    return {
        "schema_version": 2,
        "template_id": data.get("template_id") or DEFAULT_TEMPLATE_ID,
        "personal": dict(data.get("personal") or {}) if isinstance(data.get("personal"), dict) else {},
        "summary": data.get("summary", ""),
        "experience": list(data.get("experience") or []) if isinstance(data.get("experience"), list) else [],
        "projects": list(data.get("projects") or []) if isinstance(data.get("projects"), list) else [],
        "technical_skills": dict(data.get("technical_skills") or {}) if isinstance(data.get("technical_skills"), dict) else {},
        "certifications": list(data.get("certifications") or []) if isinstance(data.get("certifications"), list) else [],
        "education": list(data.get("education") or []) if isinstance(data.get("education"), list) else [],
    }


def _empty_v2():
    """Return a minimal valid v2 skeleton (for malformed input)."""
    return {
        "schema_version": 2,
        "template_id": DEFAULT_TEMPLATE_ID,
        "personal": {
            "full_name": "",
            "email": "",
            "phone": "",
            "linkedin": "",
            "location": "",
            "github": None,
            "portfolio": None,
        },
        "summary": "",
        "experience": [],
        "projects": [],
        "technical_skills": {"_custom": []},
        "certifications": [],
        "education": [],
    }


def _str_or_empty(v):
    """Coerce to string; None/non-string -> empty string."""
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    # Defensive: numbers, bools, etc. -> string repr
    return str(v)
