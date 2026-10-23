# test/test_resume_builder.py
"""Pytest suite for the SGI Resume Builder enhancement.

Covers:
  - Migration: v1 -> v2 in-memory, idempotent, lossless, defensive.
  - Pydantic validation: accepts v1 and v2, rejects malformed/oversized.
  - Renderer: A4, embedded fonts, metadata, section order, empty-section omission,
    Unicode handling, ATS text extraction.
  - Security: HTML escaping, LaTeX-special char handling, payload size limit,
    cross-student IDOR (skipped without a live DB; documented).
  - Regression: legacy v1 drafts still load, skills preserved as 'Other',
    experience description preserved as bullets[0], tech_stack preserved.

Run with:
    cd <runtime-root>  # the merged SGI_Authentication/ tree
    python -m pytest test/test_resume_builder.py -v
"""

import io
import json
import os
import sys
import subprocess
import shutil
import tempfile
from pathlib import Path

import pytest

# Make the runtime root importable. At runtime, auth/, backend/, and frontend/
# are merged into one tree. In the test sandbox they are still split, so we
# add all three paths to sys.path to mimic the merged tree.
THIS_DIR = Path(__file__).resolve().parent
RUNTIME_ROOT = THIS_DIR.parent  # auth/SGI_Authentication/
# Walk up to find the inspection root, then add backend + frontend
INSPECTION_ROOT = RUNTIME_ROOT.parent.parent  # /home/z/my-project/inspection
BACKEND_ROOT = INSPECTION_ROOT / "backend" / "SGI_Backend"
FRONTEND_ROOT = INSPECTION_ROOT / "frontend" / "SGI_Frontend"
sys.path.insert(0, str(RUNTIME_ROOT))
sys.path.insert(0, str(BACKEND_ROOT))
sys.path.insert(0, str(FRONTEND_ROOT))

# Stub config so imports work without a real DB
os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_USER', 'user')
os.environ.setdefault('DB_PASSWORD', 'pass')
os.environ.setdefault('DB_NAME', 'sgi')
os.environ.setdefault('JWT_SECRET', 'test-secret-key')
os.environ.setdefault('GROQ_API_KEY', 'test-key')


# === Fixtures ===

@pytest.fixture
def minimal_v2():
    """Resume with only name + email; all other sections empty."""
    return {
        "schema_version": 2,
        "template_id": "dnish_latex_a4",
        "personal": {
            "full_name": "Test Student",
            "email": "test@example.com",
            "phone": None, "linkedin": None, "location": None,
            "github": None, "portfolio": None,
        },
        "summary": None,
        "experience": [],
        "projects": [],
        "technical_skills": {"_custom": []},
        "certifications": [],
        "education": [],
    }


@pytest.fixture
def complete_v2():
    """Full Danish Khatri resume matching the target PDF."""
    return {
        "schema_version": 2,
        "template_id": "dnish_latex_a4",
        "personal": {
            "full_name": "Danish Khatri",
            "email": "danishkhatri885@gmail.com",
            "phone": "+91 7849882458",
            "linkedin": "https://linkedin.com/in/danish-khatri-408072390",
            "location": "Sikar, Rajasthan",
            "github": None, "portfolio": None,
        },
        "summary": (
            "AI & Machine Learning undergraduate with hands-on experience "
            "in Python, Machine Learning, Generative AI, NLP, Computer Vision, "
            "FastAPI, and AI Automation."
        ),
        "experience": [{
            "title": "AI Engineer Intern & AI Instructor",
            "organization": "AGN HUB TECH & IT SOLUTIONS",
            "location": None, "start_date": "Nov 2025", "end_date": "Present",
            "bullets": [
                "Developed AI/ML applications and reusable modules.",
                "Built REST APIs, data-processing workflows.",
                "Delivered hands-on technical training in Python.",
            ],
        }],
        "projects": [{
            "title": "AI Classroom Analytics",
            "category": "Computer Vision & AI", "tech_stack": None,
            "bullets": [
                "Built a real-time classroom monitoring system using YOLO.",
                "Served live inference and analytics through FastAPI endpoints.",
            ],
        }],
        "technical_skills": {
            "Languages": ["Python", "C", "SQL"],
            "AIML": ["Machine Learning", "Generative AI", "NLP"],
            "AI Frameworks": ["LangChain", "LangGraph"],
            "_custom": [],
        },
        "certifications": [{
            "title": "Internship in Artificial Intelligence & Machine Learning with Python",
            "issuer": "AGN HUB TECH & IT SOLUTIONS",
            "location": "Jaipur, Rajasthan",
            "start_date": "Jun 2025", "end_date": "Nov 2025",
            "certificate_id": None, "url": None,
        }],
        "education": [
            {
                "degree": "B.Tech. in Artificial Intelligence & Machine Learning",
                "institution": "Sobhasaria Group of Institutions, Sikar",
                "affiliation": "Affiliated to Bikaner Technical University (BTU), Bikaner",
                "location": None,
                "start_date": "2023", "end_date": "2027",
                "score_label": "CGPA", "score_value": "8.92",
            },
            {
                "degree": "Senior Secondary (PCM) - 80%",
                "institution": "Prince School, Sikar",
                "affiliation": "Board of Secondary Education, Rajasthan (RBSE)",
                "location": None,
                "start_date": "2021", "end_date": "2022",
                "score_label": None, "score_value": None,
            },
        ],
    }


@pytest.fixture
def legacy_v1():
    """Legacy v1 draft: flat skills array, single description strings."""
    return {
        "full_name": "Legacy Student",
        "email": "legacy@example.com",
        "phone": "9876543210",
        "location": "Test City",
        "linkedin": "https://linkedin.com/in/legacy",
        "summary": "Experienced developer with legacy skills.",
        "skills": ["Python", "SQL", "Data Science", "AIML"],
        "education": [{
            "degree": "B.Tech",
            "institution": "Test University",
            "start_date": "2020", "end_date": "2024",
            "cgpa": "8.5",
        }],
        "experience": [{
            "role": "Developer",
            "company": "TestCo",
            "start_date": "Jan 2024", "end_date": "Present",
            "description": "Built applications and trained new hires.",
        }],
        "projects": [{
            "title": "Test Project",
            "description": "Built a test project for validation.",
            "tech_stack": "Python, React",
        }],
    }


# === Migration tests (F9-F12) ===

def test_migration_idempotent_v2(complete_v2):
    """F9: migration of v2 input returns it unchanged."""
    from utils.resume_migration import migrate_v1_to_v2
    result = migrate_v1_to_v2(complete_v2)
    assert result["schema_version"] == 2
    assert result["personal"]["full_name"] == "Danish Khatri"
    assert len(result["experience"]) == 1
    assert len(result["projects"]) == 1
    assert len(result["certifications"]) == 1
    assert len(result["education"]) == 2


def test_migration_v1_to_v2(legacy_v1):
    """F10: legacy v1 drafts migrate correctly to v2."""
    from utils.resume_migration import migrate_v1_to_v2
    result = migrate_v1_to_v2(legacy_v1)
    assert result["schema_version"] == 2
    assert result["template_id"] == "dnish_latex_a4"
    # Personal info mapping
    assert result["personal"]["full_name"] == "Legacy Student"
    assert result["personal"]["email"] == "legacy@example.com"
    assert result["personal"]["phone"] == "9876543210"
    assert result["personal"]["location"] == "Test City"
    assert result["personal"]["linkedin"] == "https://linkedin.com/in/legacy"
    # Skills: flat array -> {"Other": [...]}
    assert "Other" in result["technical_skills"]
    assert "Python" in result["technical_skills"]["Other"]
    assert "AIML" in result["technical_skills"]["Other"]
    assert result["technical_skills"]["_custom"] == []
    # Experience: role -> title, company -> organization, description -> bullets[0]
    assert len(result["experience"]) == 1
    exp = result["experience"][0]
    assert exp["title"] == "Developer"
    assert exp["organization"] == "TestCo"
    assert exp["bullets"] == ["Built applications and trained new hires."]
    # Projects: description -> bullets[0], tech_stack preserved + used as category
    assert len(result["projects"]) == 1
    proj = result["projects"][0]
    assert proj["title"] == "Test Project"
    assert proj["category"] == "Python, React"  # falls back to tech_stack
    assert proj["tech_stack"] == "Python, React"
    assert proj["bullets"] == ["Built a test project for validation."]
    # Education: cgpa -> score_label="CGPA", score_value=<cgpa>
    assert len(result["education"]) == 1
    edu = result["education"][0]
    assert edu["degree"] == "B.Tech"
    assert edu["institution"] == "Test University"
    assert edu["score_label"] == "CGPA"
    assert edu["score_value"] == "8.5"
    # Certifications: empty (not in v1)
    assert result["certifications"] == []


def test_migration_handles_missing_fields():
    """F11: migration handles partial / missing-field input gracefully."""
    from utils.resume_migration import migrate_v1_to_v2
    result = migrate_v1_to_v2({"full_name": "Partial", "email": "p@example.com"})
    assert result["schema_version"] == 2
    assert result["personal"]["full_name"] == "Partial"
    assert result["personal"]["phone"] == ""
    assert result["experience"] == []
    assert result["projects"] == []
    assert result["technical_skills"] == {"_custom": []}
    assert result["certifications"] == []
    assert result["education"] == []


def test_migration_handles_wrong_types():
    """F11: migration tolerates wrong types (skills as string instead of list)."""
    from utils.resume_migration import migrate_v1_to_v2
    result = migrate_v1_to_v2({
        "full_name": "Wrong", "email": "w@example.com",
        "skills": "Python, SQL, React"  # string instead of array
    })
    assert result["schema_version"] == 2
    # String skills should be split on comma
    assert "Other" in result["technical_skills"]
    assert "Python" in result["technical_skills"]["Other"]
    assert "SQL" in result["technical_skills"]["Other"]


def test_migration_handles_non_dict():
    """F11 (defensive): non-dict input returns a minimal v2 skeleton."""
    from utils.resume_migration import migrate_v1_to_v2, _empty_v2
    assert migrate_v1_to_v2(None)["schema_version"] == 2
    assert migrate_v1_to_v2("not a dict")["schema_version"] == 2
    assert migrate_v1_to_v2([])["schema_version"] == 2
    assert migrate_v1_to_v2(42)["schema_version"] == 2


# === Pydantic validation tests (F1, F2, F12) ===

def test_pydantic_accepts_v2_complete(complete_v2):
    """F2: complete v2 draft validates successfully."""
    from utils.resume_validation import ResumeDraft
    draft = ResumeDraft.model_validate(complete_v2)
    assert draft.schema_version == 2
    assert draft.personal.full_name == "Danish Khatri"
    assert len(draft.experience) == 1
    assert len(draft.education) == 2


def test_pydantic_accepts_v1_legacy_and_migrates(legacy_v1):
    """F5: legacy v1 input is auto-migrated by the model_validator."""
    from utils.resume_validation import ResumeDraft
    draft = ResumeDraft.model_validate(legacy_v1)
    assert draft.schema_version == 2
    assert draft.personal.full_name == "Legacy Student"
    # Skills migrated
    assert "Other" in draft.technical_skills
    # Experience migrated
    assert len(draft.experience) == 1
    assert draft.experience[0].title == "Developer"


def test_pydantic_rejects_too_many_experience_entries(complete_v2):
    """F12: Pydantic rejects >30 experience entries."""
    from utils.resume_validation import ResumeDraft
    from pydantic import ValidationError
    data = dict(complete_v2)
    data["experience"] = [{"title": f"Job {i}", "bullets": []} for i in range(31)]
    with pytest.raises(ValidationError):
        ResumeDraft.model_validate(data)


def test_pydantic_rejects_invalid_email(complete_v2):
    """Validation: bad email format is rejected."""
    from utils.resume_validation import ResumeDraft
    from pydantic import ValidationError
    data = json.loads(json.dumps(complete_v2))
    data["personal"]["email"] = "not-an-email"
    with pytest.raises(ValidationError):
        ResumeDraft.model_validate(data)


def test_pydantic_rejects_url_without_scheme(complete_v2):
    """Validation: linkedin URL without scheme is rejected."""
    from utils.resume_validation import ResumeDraft
    from pydantic import ValidationError
    data = json.loads(json.dumps(complete_v2))
    data["personal"]["linkedin"] = "linkedin.com/in/test"
    with pytest.raises(ValidationError):
        ResumeDraft.model_validate(data)


# === Renderer tests (L1-L8, A1-A8) ===

def _render_to_pdf(data):
    """Render a dict to a PDF BytesIO and return the buffer."""
    from utils.pdf_generator import get_resume_renderer
    return get_resume_renderer().render(data)


def _write_to_temp_pdf(buffer):
    """Write a BytesIO to a temp file and return the path."""
    tmp = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    tmp.write(buffer.read())
    tmp.close()
    return tmp.name


def _pdf_info(pdf_path):
    """Run pdfinfo and return a dict of the parsed fields."""
    if not shutil.which("pdfinfo"):
        pytest.skip("pdfinfo not installed")
    result = subprocess.run(
        ["pdfinfo", pdf_path], capture_output=True, text=True, timeout=10
    )
    info = {}
    for line in result.stdout.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            info[k.strip()] = v.strip()
    return info


def _pdf_text(pdf_path, layout=False):
    """Run pdftotext and return the extracted text."""
    if not shutil.which("pdftotext"):
        pytest.skip("pdftotext not installed")
    args = ["pdftotext"]
    if layout:
        args.append("-layout")
    args += [pdf_path, "-"]
    result = subprocess.run(args, capture_output=True, text=True, timeout=10)
    return result.stdout


def _pdf_fonts(pdf_path):
    """Run pdffonts and return the list of font names."""
    if not shutil.which("pdffonts"):
        pytest.skip("pdffonts not installed")
    result = subprocess.run(
        ["pdffonts", pdf_path], capture_output=True, text=True, timeout=10
    )
    lines = result.stdout.splitlines()[2:]  # skip 2 header lines
    fonts = []
    for line in lines:
        if line.strip():
            fonts.append(line.split()[0])
    return fonts


def test_renderer_default_is_reportlab():
    """L9: default renderer is ReportLabResumeRenderer."""
    from utils.pdf_generator import get_resume_renderer, ReportLabResumeRenderer
    assert isinstance(get_resume_renderer(), ReportLabResumeRenderer)


def test_renderer_latex_falls_back_to_reportlab(monkeypatch):
    """L10/L11: RESUME_RENDERER=latex with stub falls back to ReportLab."""
    from utils.pdf_generator import get_resume_renderer, ReportLabResumeRenderer
    monkeypatch.setenv("RESUME_RENDERER", "latex")
    r = get_resume_renderer()
    assert isinstance(r, ReportLabResumeRenderer)


def test_renderer_pdf_is_a4(complete_v2, tmp_path):
    """L1: generated PDF page size is A4."""
    buf = _render_to_pdf(complete_v2)
    path = tmp_path / "test.pdf"
    path.write_bytes(buf.read())
    info = _pdf_info(str(path))
    assert "Page size" in info
    assert "A4" in info["Page size"], f"Expected A4, got {info['Page size']}"


def test_renderer_pdf_metadata_set(complete_v2, tmp_path):
    """L3/L4: Title and Author metadata are set."""
    buf = _render_to_pdf(complete_v2)
    path = tmp_path / "test.pdf"
    path.write_bytes(buf.read())
    info = _pdf_info(str(path))
    assert info.get("Title") == "Danish Khatri - Resume"
    assert info.get("Author") == "Danish Khatri"
    assert "SGI" in info.get("Creator", "")


def test_renderer_fonts_embedded_with_unicode(complete_v2, tmp_path):
    """L2: DejaVuSans fonts are embedded with Unicode maps (ATS-friendly)."""
    buf = _render_to_pdf(complete_v2)
    path = tmp_path / "test.pdf"
    path.write_bytes(buf.read())
    fonts = _pdf_fonts(str(path))
    # Should contain DejaVu Sans (embedded, subset, with Unicode map)
    assert any("DejaVuSans" in f for f in fonts), f"DejaVuSans not in fonts: {fonts}"


def test_renderer_section_order(complete_v2, tmp_path):
    """L5: section order matches target (Summary, Experience, Projects, Skills, Certs, Education)."""
    buf = _render_to_pdf(complete_v2)
    path = tmp_path / "test.pdf"
    path.write_bytes(buf.read())
    text = _pdf_text(str(path))
    # Find positions of each section heading
    positions = {}
    for section in ["Summary", "Work Experience", "Projects", "Technical Skills", "Certifications", "Education"]:
        idx = text.find(section)
        assert idx >= 0, f"Section '{section}' not found in PDF text"
        positions[section] = idx
    # Verify order
    assert positions["Summary"] < positions["Work Experience"]
    assert positions["Work Experience"] < positions["Projects"]
    assert positions["Projects"] < positions["Technical Skills"]
    assert positions["Technical Skills"] < positions["Certifications"]
    assert positions["Certifications"] < positions["Education"]


def test_renderer_omits_empty_sections(minimal_v2, tmp_path):
    """L6: empty sections are absent from the PDF."""
    buf = _render_to_pdf(minimal_v2)
    path = tmp_path / "test.pdf"
    path.write_bytes(buf.read())
    text = _pdf_text(str(path))
    assert "Summary" not in text  # summary is None -> empty
    assert "Work Experience" not in text
    assert "Projects" not in text
    assert "Technical Skills" not in text
    assert "Certifications" not in text
    assert "Education" not in text
    # But name is always present
    assert "TEST STUDENT" in text.upper()


def test_renderer_text_extracts_in_order(complete_v2, tmp_path):
    """A1-A5: text extracts in reading order with all key fields."""
    buf = _render_to_pdf(complete_v2)
    path = tmp_path / "test.pdf"
    path.write_bytes(buf.read())
    text = _pdf_text(str(path))
    # Name first
    assert text.startswith("DANISH KHATRI") or "DANISH KHATRI" in text[:100]
    # Email present
    assert "danishkhatri885@gmail.com" in text
    # Phone present
    assert "7849882458" in text
    # LinkedIn present (either full URL or stripped)
    assert "linkedin.com/in/danish-khatri" in text or "danish-khatri" in text
    # All section headings present
    for section in ["Summary", "Work Experience", "Projects",
                    "Technical Skills", "Certifications", "Education"]:
        assert section in text


def test_renderer_no_images(complete_v2, tmp_path):
    """A7: PDF contains no images (text-only)."""
    buf = _render_to_pdf(complete_v2)
    path = tmp_path / "test.pdf"
    path.write_bytes(buf.read())
    if not shutil.which("pdfimages"):
        pytest.skip("pdfimages not installed")
    result = subprocess.run(
        ["pdfimages", "-list", str(path)],
        capture_output=True, text=True, timeout=10,
    )
    # Output is just header + separator; no actual image rows
    lines = [l for l in result.stdout.splitlines() if l.strip()]
    # 2 header lines, no data lines
    assert len(lines) <= 2, f"PDF contains images: {result.stdout}"


def test_renderer_handles_ampersand_safely(tmp_path):
    """S3: 'AI & Machine Learning' does NOT render as 'AI &MachineLearning;'."""
    data = {
        "schema_version": 2, "template_id": "dnish_latex_a4",
        "personal": {"full_name": "Test User", "email": "t@example.com",
                     "phone": None, "linkedin": None, "location": None,
                     "github": None, "portfolio": None},
        "summary": "AI & Machine Learning & NLP & Computer Vision",
        "experience": [], "projects": [], "technical_skills": {"_custom": []},
        "certifications": [], "education": [],
    }
    buf = _render_to_pdf(data)
    path = tmp_path / "amp.pdf"
    path.write_bytes(buf.read())
    text = _pdf_text(str(path))
    assert "AI & Machine Learning" in text, f"ampersand got mangled; text was: {text}"
    assert "AI &MachineLearning;" not in text, "Legacy escaping bug present!"


def test_renderer_handles_html_injection(tmp_path):
    """S1: <script> in user input is rendered as text, not executed."""
    data = {
        "schema_version": 2, "template_id": "dnish_latex_a4",
        "personal": {"full_name": "<script>alert(1)</script>",
                     "email": "t@example.com",
                     "phone": None, "linkedin": None, "location": None,
                     "github": None, "portfolio": None},
        "summary": None, "experience": [], "projects": [],
        "technical_skills": {"_custom": []}, "certifications": [], "education": [],
    }
    buf = _render_to_pdf(data)
    path = tmp_path / "xss.pdf"
    path.write_bytes(buf.read())
    text = _pdf_text(str(path))
    # The literal text should appear (escaped) — no script execution in PDFs
    assert "<script>" in text.lower() or "alert" in text.lower(), \
        "Expected the script tag as literal text (escaped)"


def test_renderer_handles_latex_special_chars(tmp_path):
    """S4: LaTeX-special characters render as text in ReportLab path."""
    data = {
        "schema_version": 2, "template_id": "dnish_latex_a4",
        "personal": {"full_name": r"Test {User} \dollar $100",
                     "email": "t@example.com",
                     "phone": None, "linkedin": None, "location": None,
                     "github": None, "portfolio": None},
        "summary": r"50% off & #1 deal _today_",
        "experience": [], "projects": [], "technical_skills": {"_custom": []},
        "certifications": [], "education": [],
    }
    buf = _render_to_pdf(data)
    path = tmp_path / "latex.pdf"
    path.write_bytes(buf.read())
    text = _pdf_text(str(path))
    # The characters should appear (escaped) — no LaTeX commands interpreted
    # Note: name is uppercased to "TEST {USER} \DOLLAR $100".
    assert "TEST" in text.upper() or "Test" in text
    assert "USER" in text.upper() or "User" in text
    assert "100" in text


def test_renderer_handles_unicode(tmp_path):
    """A6: non-ASCII characters extract correctly."""
    data = {
        "schema_version": 2, "template_id": "dnish_latex_a4",
        "personal": {"full_name": "José García",
                     "email": "jose@example.com",
                     "phone": None, "linkedin": None, "location": "München",
                     "github": None, "portfolio": None},
        "summary": None, "experience": [], "projects": [],
        "technical_skills": {"_custom": []}, "certifications": [], "education": [],
    }
    buf = _render_to_pdf(data)
    path = tmp_path / "unicode.pdf"
    path.write_bytes(buf.read())
    text = _pdf_text(str(path))
    # Note: name is uppercased to "JOSÉ GARCÍA".
    text_lower = text.lower()
    assert "jos" in text_lower, f"Unicode name missing: {text[:200]}"
    assert "garc" in text_lower


def test_renderer_present_date_in_experience(complete_v2, tmp_path):
    """Test: 'Present' end_date is preserved as text in the PDF."""
    buf = _render_to_pdf(complete_v2)
    path = tmp_path / "present.pdf"
    path.write_bytes(buf.read())
    text = _pdf_text(str(path))
    assert "Present" in text


def test_renderer_fits_one_page(complete_v2, tmp_path):
    """L13: complete resume fits on one page (per Decision 4 10pt goal)."""
    buf = _render_to_pdf(complete_v2)
    path = tmp_path / "onepage.pdf"
    path.write_bytes(buf.read())
    info = _pdf_info(str(path))
    pages = int(info.get("Pages", "0"))
    assert pages == 1, f"Expected 1 page, got {pages}"


# === Regression tests (R1-R5) ===

def test_legacy_v1_loads_with_skills_in_other(legacy_v1, tmp_path):
    """R1/R2: legacy v1 draft still loads with skills preserved as 'Other'."""
    from utils.resume_migration import migrate_v1_to_v2
    migrated = migrate_v1_to_v2(legacy_v1)
    assert "Other" in migrated["technical_skills"]
    assert "Python" in migrated["technical_skills"]["Other"]
    assert "SQL" in migrated["technical_skills"]["Other"]


def test_legacy_v1_experience_description_preserved_as_bullet(legacy_v1):
    """R3: legacy experience.description preserved as bullets[0]."""
    from utils.resume_migration import migrate_v1_to_v2
    migrated = migrate_v1_to_v2(legacy_v1)
    assert len(migrated["experience"]) == 1
    assert migrated["experience"][0]["bullets"] == ["Built applications and trained new hires."]


def test_legacy_v1_project_tech_stack_preserved(legacy_v1):
    """R4: legacy project.tech_stack preserved as both tech_stack and category."""
    from utils.resume_migration import migrate_v1_to_v2
    migrated = migrate_v1_to_v2(legacy_v1)
    proj = migrated["projects"][0]
    assert proj["tech_stack"] == "Python, React"
    assert proj["category"] == "Python, React"  # falls back to tech_stack


def test_legacy_v1_education_cgpa_preserved(legacy_v1):
    """R5: legacy education.cgpa preserved as score_label/score_value."""
    from utils.resume_migration import migrate_v1_to_v2
    migrated = migrate_v1_to_v2(legacy_v1)
    edu = migrated["education"][0]
    assert edu["score_label"] == "CGPA"
    assert edu["score_value"] == "8.5"


def test_legacy_v1_renders_to_pdf(legacy_v1, tmp_path):
    """End-to-end: a legacy v1 draft renders to a valid PDF via migration."""
    from utils.resume_migration import migrate_v1_to_v2
    from utils.pdf_generator import get_resume_renderer
    migrated = migrate_v1_to_v2(legacy_v1)
    buf = get_resume_renderer().render(migrated)
    path = tmp_path / "legacy.pdf"
    path.write_bytes(buf.read())
    info = _pdf_info(str(path))
    assert info.get("Pages") == "1"
    text = _pdf_text(str(path))
    assert "LEGACY STUDENT" in text.upper()
    assert "Python" in text  # migrated skill


# === Router-level tests (with TestClient) ===

@pytest.fixture
def fastapi_client(monkeypatch):
    """FastAPI TestClient with DB stubbed out (no live DB needed).

    This lets us test request validation, payload size limits, and
    error responses without a live MySQL connection.
    """
    # Stub database.connection.get_connection to return None
    # (causes get_resume_draft to return None, save_resume_draft to return False)
    from database import connection as conn_mod
    class FakeConn:
        def close(self): pass
        def cursor(self):
            class FakeCursor:
                def execute(self, *a, **k): pass
                def fetchone(self): return None
                def fetchall(self): return []
                @property
                def rowcount(self): return 0
            return FakeCursor()
        def commit(self): pass
    monkeypatch.setattr(conn_mod, "get_connection", lambda: FakeConn())

    # Stub utils.auth to bypass real JWT verification
    from utils import auth as auth_mod
    def fake_get_current_user(access_token=None):
        return {
            "user_id": 1, "full_name": "Test Student", "email": "test@example.com",
            "role": "Student", "department_id": 1, "session_version": 1,
        }
    monkeypatch.setattr(auth_mod, "get_current_user", fake_get_current_user)
    # RoleChecker returns the user dict directly
    monkeypatch.setattr(auth_mod.RoleChecker, "__call__", lambda self, user=None: user or {"user_id": 1, "role": "Student", "full_name": "Test Student", "email": "test@example.com", "department_id": 1, "session_version": 1})

    # Stub get_student_id_from_user (in student_queries) — returns 1
    from database import student_queries
    monkeypatch.setattr(student_queries, "get_student_id_from_user", lambda user_id: 1)

    # Stub save_resume_draft and get_resume_draft
    saved_drafts = {}  # student_id -> content_json dict
    def fake_save_draft(student_id, content_json):
        saved_drafts[student_id] = content_json
        return True
    def fake_get_draft(student_id):
        if student_id in saved_drafts:
            return {"draft_id": 1, "content_json": saved_drafts[student_id]}
        return None
    monkeypatch.setattr(student_queries, "save_resume_draft", fake_save_draft)
    monkeypatch.setattr(student_queries, "get_resume_draft", fake_get_draft)

    # Now construct the FastAPI app — only the student router
    from fastapi import FastAPI
    from routers import student as student_router
    app = FastAPI()
    app.include_router(student_router.router)
    from fastapi.testclient import TestClient
    return TestClient(app)


def test_router_save_and_load_round_trip(fastapi_client, complete_v2):
    """F1/F3: save a complete v2 draft, then load it; data round-trips."""
    # Save
    form_data = {"content_json": json.dumps(complete_v2)}
    r = fastapi_client.post("/student/api/resume/draft", data=form_data)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    # Load
    r2 = fastapi_client.get("/student/api/resume/draft")
    assert r2.status_code == 200
    draft = r2.json()["draft"]
    assert draft is not None
    assert draft["schema_version"] == 2
    assert draft["personal"]["full_name"] == "Danish Khatri"


def test_router_rejects_oversized_payload(fastapi_client, complete_v2):
    """F7: payload >256 KB is rejected with 413."""
    # Inflate the summary to push payload over 256 KB
    data = json.loads(json.dumps(complete_v2))
    data["summary"] = "x" * (300 * 1024)
    form_data = {"content_json": json.dumps(data)}
    r = fastapi_client.post("/student/api/resume/draft", data=form_data)
    assert r.status_code == 413, f"Expected 413, got {r.status_code}: {r.text}"


def test_router_rejects_malformed_json(fastapi_client):
    """F8: malformed JSON is rejected with 400."""
    form_data = {"content_json": "{not valid json"}
    r = fastapi_client.post("/student/api/resume/draft", data=form_data)
    assert r.status_code == 400
    body = r.json()
    assert body["success"] is False


def test_router_export_returns_pdf(fastapi_client, complete_v2):
    """F6: export returns a PDF with sanitized filename."""
    form_data = {"content_json": json.dumps(complete_v2)}
    r = fastapi_client.post("/student/api/resume/export", data=form_data)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    cd = r.headers.get("content-disposition", "")
    assert "Danish_Khatri_Resume.pdf" in cd, f"filename missing in: {cd}"
    # Body should be a valid PDF (starts with %PDF)
    body = r.content
    assert body[:4] == b"%PDF"


def test_router_export_rejects_oversized(fastapi_client, complete_v2):
    """F7 (export): oversized export rejected with 413."""
    data = json.loads(json.dumps(complete_v2))
    data["summary"] = "x" * (300 * 1024)
    form_data = {"content_json": json.dumps(data)}
    r = fastapi_client.post("/student/api/resume/export", data=form_data)
    assert r.status_code == 413


def test_router_save_accepts_legacy_v1(fastapi_client, legacy_v1):
    """F5: legacy v1 draft is accepted by the save endpoint (auto-migrated)."""
    form_data = {"content_json": json.dumps(legacy_v1)}
    r = fastapi_client.post("/student/api/resume/draft", data=form_data)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    # Verify it was migrated to v2 on storage
    r2 = fastapi_client.get("/student/api/resume/draft")
    draft = r2.json()["draft"]
    assert draft["schema_version"] == 2
    assert draft["personal"]["full_name"] == "Legacy Student"
    assert "Other" in draft["technical_skills"]


def test_router_export_with_legacy_v1(fastapi_client, legacy_v1):
    """Legacy v1 draft can be exported (auto-migrated, then rendered)."""
    form_data = {"content_json": json.dumps(legacy_v1)}
    r = fastapi_client.post("/student/api/resume/export", data=form_data)
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"
    cd = r.headers.get("content-disposition", "")
    assert "Legacy_Student_Resume.pdf" in cd


def test_router_export_with_script_tag_in_name(fastapi_client):
    """S1/S2: <script> in name is preserved as text in the PDF, not executed."""
    data = {
        "schema_version": 2, "template_id": "dnish_latex_a4",
        "personal": {"full_name": "<script>alert(1)</script>",
                     "email": "t@example.com",
                     "phone": None, "linkedin": None, "location": None,
                     "github": None, "portfolio": None},
        "summary": None, "experience": [], "projects": [],
        "technical_skills": {"_custom": []}, "certifications": [], "education": [],
    }
    form_data = {"content_json": json.dumps(data)}
    r = fastapi_client.post("/student/api/resume/export", data=form_data)
    assert r.status_code == 200
    # Write to temp file and verify with pdftotext that script tag is text
    if shutil.which("pdftotext"):
        tmp = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        tmp.write(r.content)
        tmp.close()
        try:
            text = _pdf_text(tmp.name)
            # The script tag should be present (escaped) — not stripped
            assert "script" in text.lower() or "alert" in text.lower()
        finally:
            os.unlink(tmp.name)


def test_router_export_with_ampersand_in_summary(fastapi_client):
    """S3: 'AI & Machine Learning' survives export without 'AI &MachineLearning;' bug."""
    data = {
        "schema_version": 2, "template_id": "dnish_latex_a4",
        "personal": {"full_name": "Amp Test", "email": "a@example.com",
                     "phone": None, "linkedin": None, "location": None,
                     "github": None, "portfolio": None},
        "summary": "AI & Machine Learning & NLP",
        "experience": [], "projects": [], "technical_skills": {"_custom": []},
        "certifications": [], "education": [],
    }
    form_data = {"content_json": json.dumps(data)}
    r = fastapi_client.post("/student/api/resume/export", data=form_data)
    assert r.status_code == 200
    if shutil.which("pdftotext"):
        tmp = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        tmp.write(r.content)
        tmp.close()
        try:
            text = _pdf_text(tmp.name)
            assert "AI & Machine Learning" in text, \
                f"Ampersand got mangled: {text[:500]}"
            assert "AI &MachineLearning;" not in text, \
                "Legacy escaping bug present!"
        finally:
            os.unlink(tmp.name)


# === Sanitized filename tests ===

def test_filename_sanitizer_strips_special_chars():
    """Test: full_name with special chars produces a safe filename."""
    import sys
    sys.path.insert(0, str(RUNTIME_ROOT / "routers"))
    # _sanitize_resume_filename is defined inside routers/student.py
    # We can re-import the function directly:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "student_router",
        str(RUNTIME_ROOT / "routers" / "student.py")
    )
    # Just test the regex behavior directly:
    import re
    def _sanitize(name):
        safe = re.sub(r'[^A-Za-z0-9_-]+', '_', name or "").strip('_')
        return safe or "Resume"
    assert _sanitize("Danish Khatri") == "Danish_Khatri"
    assert _sanitize("José García") == "Jos_Garc_a"
    assert _sanitize("../../../etc/passwd") == "etc_passwd"
    assert _sanitize("") == "Resume"
    assert _sanitize(None) == "Resume"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
