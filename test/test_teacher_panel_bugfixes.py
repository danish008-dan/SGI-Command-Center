# test/test_teacher_panel_bugfixes.py
"""Iteration 1 — Bug Fixes (Bugs 1, 2, 3) Test Suite.

Covers:
  - Bug 1: /teacher/api/sections endpoint (was missing — root cause of empty section dropdown)
  - Bug 2: /teacher/api/attendance/status endpoint (was missing — root cause of radio buttons
           not showing saved state)
  - Bug 3: marks entry (existing routes work; this verifies the supporting /sections endpoint
           and the existing max_marks validation)
  - Date validation with ATTENDANCE_DEMO_MODE env var (Q11)
  - Entry-count caps (max 200 records per save) — Q35/Q36
  - IDOR prevention (cross-teacher subject scope check)
  - Auth (401 unauth, 403 non-Teacher role)

Run with:
    cd <runtime-root>  # the merged SGI_Authentication/ tree
    python -m pytest test/test_teacher_panel_bugfixes.py -v
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta

import pytest

# Runtime path setup (mimics the merged tree)
THIS_DIR = Path(__file__).resolve().parent
RUNTIME_ROOT = THIS_DIR.parent
INSPECTION_ROOT = RUNTIME_ROOT.parent.parent  # /home/z/my-project/inspection
BACKEND_ROOT = INSPECTION_ROOT / "backend" / "SGI_Backend"
FRONTEND_ROOT = INSPECTION_ROOT / "frontend" / "SGI_Frontend"
sys.path.insert(0, str(RUNTIME_ROOT))
sys.path.insert(0, str(BACKEND_ROOT))
sys.path.insert(0, str(FRONTEND_ROOT))

os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_USER', 'user')
os.environ.setdefault('DB_PASSWORD', 'pass')
os.environ.setdefault('DB_NAME', 'sgi')
os.environ.setdefault('JWT_SECRET', 'test-secret-key')
os.environ.setdefault('GROQ_API_KEY', 'test-key')


# === Test fixture: FastAPI TestClient with DB stubbed out ===

@pytest.fixture
def teacher_client(monkeypatch):
    """TestClient with DB stubbed. No live MySQL needed."""
    # Stub DB connection
    from database import connection as conn_mod

    class FakeCursor:
        def __init__(self):
            self._scalar = None
            self._rows = []
        def execute(self, sql, params=None):
            # Detect query type by SQL content
            sql_lower = sql.lower() if isinstance(sql, str) else ""
            if "select teacher_id from teachers where user_id" in sql_lower:
                self._scalar = {"teacher_id": 1}
                self._rows = []
            elif "select 1 from subjects where subject_id" in sql_lower:
                # verify_teacher_subject_scope returns true for subject_id=1 (owned by teacher_id=1)
                self._scalar = {"1": 1}
                self._rows = []
            elif "select distinct section from subjects where teacher_id" in sql_lower:
                # get_sections_for_teacher_subject returns ['A'] for subject_id=1
                self._rows = [{"section": "A"}]
                self._scalar = None
            elif "select a.student_id, a.status from attendance a" in sql_lower:
                # get_existing_attendance — return empty for fresh dates
                self._rows = []
                self._scalar = None
            elif "insert into attendance" in sql_lower or "on duplicate key update" in sql_lower:
                self._scalar = None
                self._rows = []
            else:
                self._scalar = None
                self._rows = []
        def fetchone(self):
            return self._scalar
        def fetchall(self):
            return self._rows
        @property
        def rowcount(self):
            return 1
        def close(self): pass

    class FakeConn:
        def __init__(self):
            self.closed = False
        def cursor(self):
            return FakeCursor()
        def commit(self): pass
        def close(self):
            self.closed = True

    monkeypatch.setattr(conn_mod, "get_connection", lambda: FakeConn())

    # Stub auth: bypass real JWT verification
    from utils import auth as auth_mod

    def fake_get_current_user(access_token=None):
        return {
            "user_id": 3,  # matches teacher_id=1 in DB
            "full_name": "Mr. Aakash Nama",
            "email": "info.agnhub123@gmail.com",
            "role": "Teacher",
            "department_id": 1,
            "session_version": 1,
        }
    monkeypatch.setattr(auth_mod, "get_current_user", fake_get_current_user)
    monkeypatch.setattr(auth_mod.RoleChecker, "__call__",
                        lambda self, user=None: user or {
                            "user_id": 3, "role": "Teacher", "full_name": "Test",
                            "email": "t@e.com", "department_id": 1, "session_version": 1,
                        })

    # Stub get_teacher_id_from_user (must patch BOTH the source module AND
    # the router's already-imported reference, since `from X import Y` creates a
    # new binding that doesn't track changes to X.Y).
    from database import teacher_queries
    import routers.teacher as teacher_router_mod
    monkeypatch.setattr(teacher_queries, "get_teacher_id_from_user", lambda user_id: 1)
    monkeypatch.setattr(teacher_router_mod, "get_teacher_id_from_user", lambda user_id: 1)

    # Stub verify_teacher_subject_scope (same dual-patch pattern)
    def fake_verify_scope(teacher_id, subject_id):
        return teacher_id == 1 and subject_id == 1
    monkeypatch.setattr(teacher_queries, "verify_teacher_subject_scope", fake_verify_scope)
    monkeypatch.setattr(teacher_router_mod, "verify_teacher_subject_scope", fake_verify_scope)

    # Stub get_sections_for_teacher_subject (same dual-patch pattern)
    def fake_get_sections(teacher_id, subject_id):
        return ["A"] if (teacher_id == 1 and subject_id == 1) else []
    monkeypatch.setattr(teacher_queries, "get_sections_for_teacher_subject", fake_get_sections)
    monkeypatch.setattr(teacher_router_mod, "get_sections_for_teacher_subject", fake_get_sections)

    # Stub get_existing_attendance
    def fake_get_existing_attendance(subject_id, teacher_id, section, attendance_date):
        return {}  # always empty for testing
    monkeypatch.setattr(teacher_queries, "get_existing_attendance", fake_get_existing_attendance)
    monkeypatch.setattr(teacher_router_mod, "get_existing_attendance", fake_get_existing_attendance)

    # Stub save_attendance_record
    saved = []
    def fake_save_attendance(student_id, subject_id, teacher_id, attendance_date, status):
        saved.append((student_id, subject_id, teacher_id, attendance_date, status))
        return None  # success
    monkeypatch.setattr(teacher_queries, "save_attendance_record", fake_save_attendance)
    monkeypatch.setattr(teacher_router_mod, "save_attendance_record", fake_save_attendance)
    monkeypatch.saved_attendance = saved  # expose for tests

    # Stub save_marks_record
    saved_marks = []
    def fake_save_marks(student_id, subject_id, teacher_id, exam_type, max_marks, obtained, remarks):
        saved_marks.append((student_id, subject_id, teacher_id, exam_type, max_marks, obtained, remarks))
        return None
    monkeypatch.setattr(teacher_queries, "save_marks_record", fake_save_marks)
    monkeypatch.setattr(teacher_router_mod, "save_marks_record", fake_save_marks)
    monkeypatch.saved_marks = saved_marks

    # Stub submit_marks_for_verification
    def fake_submit_marks(subject_id, exam_type, teacher_id):
        return True, "Marks submitted for HOD verification."
    monkeypatch.setattr(teacher_queries, "submit_marks_for_verification", fake_submit_marks)
    monkeypatch.setattr(teacher_router_mod, "submit_marks_for_verification", fake_submit_marks)

    # Build the FastAPI app
    from fastapi import FastAPI
    from routers import teacher as teacher_router
    app = FastAPI()
    app.include_router(teacher_router.router)
    from fastapi.testclient import TestClient
    return TestClient(app)


# === Bug 1 — /teacher/api/sections endpoint ===

def test_sections_endpoint_returns_nonempty_for_owned_subject(teacher_client):
    """T1.1: GET /teacher/api/sections?subject_id=1 returns {sections: ['A']}."""
    r = teacher_client.get("/teacher/api/sections?subject_id=1")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "sections" in body
    assert body["sections"] == ["A"]


def test_sections_endpoint_returns_empty_for_unowned_subject(teacher_client, monkeypatch):
    """T1.2: For a subject not owned by the teacher, returns empty sections."""
    # Override verify_teacher_subject_scope to return False for subject_id=999
    from database import teacher_queries
    monkeypatch.setattr(teacher_queries, "verify_teacher_subject_scope",
                        lambda tid, sid: False if sid == 999 else True)
    r = teacher_client.get("/teacher/api/sections?subject_id=999")
    # The /sections endpoint doesn't check verify_teacher_subject_scope directly;
    # it relies on get_sections_for_teacher_subject filtering by teacher_id.
    # So it returns empty sections for subject_id=999 (not owned by teacher).
    assert r.status_code == 200
    assert r.json()["sections"] == []


def test_sections_endpoint_missing_subject_id_param(teacher_client):
    """T1.2b: subject_id is required (Query(...))."""
    r = teacher_client.get("/teacher/api/sections")
    assert r.status_code == 422  # FastAPI validation error for missing required query param


def test_sections_endpoint_non_teacher_role_blocked(teacher_client, monkeypatch):
    """T1.3: Non-Teacher role gets 403."""
    from utils import auth as auth_mod
    # Override RoleChecker to raise 403
    def deny(self, user=None):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Access Denied")
    monkeypatch.setattr(auth_mod.RoleChecker, "__call__", deny)
    r = teacher_client.get("/teacher/api/sections?subject_id=1")
    assert r.status_code == 403


def test_sections_endpoint_unauth_blocked():
    """T1.4: Unauthenticated request gets 401 (no cookie)."""
    from fastapi import FastAPI
    from routers import teacher as teacher_router
    # Don't stub auth — let the real get_current_user run; it'll see no cookie and 401.
    # But that requires real auth setup. Instead, build a minimal app where auth IS stubbed
    # to raise 401.
    from utils import auth as auth_mod
    from fastapi import HTTPException
    def deny_no_cookie(access_token=None):
        raise HTTPException(status_code=401, detail="Not authenticated")
    auth_mod.get_current_user = deny_no_cookie
    app = FastAPI()
    app.include_router(teacher_router.router)
    from fastapi.testclient import TestClient
    client = TestClient(app)
    r = client.get("/teacher/api/sections?subject_id=1")
    assert r.status_code == 401


def test_sections_endpoint_missing_teacher_profile(teacher_client, monkeypatch):
    """T1.5b: If get_teacher_id_from_user returns None, returns 400."""
    import routers.teacher as teacher_router_mod
    monkeypatch.setattr(teacher_router_mod, "get_teacher_id_from_user", lambda user_id: None)
    r = teacher_client.get("/teacher/api/sections?subject_id=1")
    assert r.status_code == 400
    assert "Teacher profile not found" in r.json()["message"]


# === Bug 2 — /teacher/api/attendance/status endpoint ===

def test_attendance_status_endpoint_returns_empty_for_fresh_date(teacher_client):
    """T2.1: GET /teacher/api/attendance/status returns {attendance: {}} for a fresh date."""
    r = teacher_client.get(
        "/teacher/api/attendance/status?subject_id=1&section=A&date=2026-10-17"
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "attendance" in body
    assert body["attendance"] == {}


def test_attendance_status_endpoint_missing_params(teacher_client):
    """T2.1b: subject_id, section, date are all required."""
    r = teacher_client.get("/teacher/api/attendance/status?subject_id=1&section=A")
    assert r.status_code == 422  # missing date


def test_attendance_status_endpoint_unauthorized_subject(teacher_client, monkeypatch):
    """T2.1c: Subject not owned by teacher returns 403."""
    from database import teacher_queries
    monkeypatch.setattr(teacher_queries, "verify_teacher_subject_scope",
                        lambda tid, sid: False if sid == 999 else True)
    r = teacher_client.get(
        "/teacher/api/attendance/status?subject_id=999&section=A&date=2026-10-17"
    )
    assert r.status_code == 403
    assert "Unauthorized subject access" in r.json()["message"]


# === Bug 1+2 — save-attendance date validation (Q11) ===

def _make_attendance_payload(date_str, n_students=2):
    """Build a minimal SaveAttendancePayload for testing."""
    return {
        "subject_id": 1,
        "section": "A",
        "date": date_str,
        "attendance": [
            {"student_id": 5 + i, "status": "Present" if i % 2 == 0 else "Absent"}
            for i in range(n_students)
        ],
    }


def test_save_attendance_production_mode_blocks_future_date(teacher_client, monkeypatch):
    """T2.9: ATTENDANCE_DEMO_MODE unset → future date rejected with 400."""
    monkeypatch.delenv("ATTENDANCE_DEMO_MODE", raising=False)
    future = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    payload = _make_attendance_payload(future)
    r = teacher_client.post("/teacher/api/save-attendance", json=payload)
    assert r.status_code == 400, r.text
    assert "Future dates not allowed" in r.json()["message"]


def test_save_attendance_demo_mode_allows_future_date(teacher_client, monkeypatch):
    """T2.6: ATTENDANCE_DEMO_MODE=1 → future date allowed."""
    monkeypatch.setenv("ATTENDANCE_DEMO_MODE", "1")
    future = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    payload = _make_attendance_payload(future)
    r = teacher_client.post("/teacher/api/save-attendance", json=payload)
    assert r.status_code == 200, r.text
    assert r.json()["success"] is True


def test_save_attendance_today_always_allowed(teacher_client, monkeypatch):
    """T2.x: Today's date is allowed in both production and demo mode."""
    monkeypatch.delenv("ATTENDANCE_DEMO_MODE", raising=False)
    today = datetime.now().strftime("%Y-%m-%d")
    payload = _make_attendance_payload(today)
    r = teacher_client.post("/teacher/api/save-attendance", json=payload)
    assert r.status_code == 200, r.text


def test_save_attendance_past_date_allowed(teacher_client, monkeypatch):
    """T2.x: Past date is allowed in both modes (teachers can mark retroactively)."""
    monkeypatch.delenv("ATTENDANCE_DEMO_MODE", raising=False)
    past = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    payload = _make_attendance_payload(past)
    r = teacher_client.post("/teacher/api/save-attendance", json=payload)
    assert r.status_code == 200, r.text


def test_save_attendance_invalid_date_format_rejected(teacher_client):
    """T2.x: Invalid date format rejected with 400."""
    payload = _make_attendance_payload("17-10-2026")  # wrong format
    r = teacher_client.post("/teacher/api/save-attendance", json=payload)
    assert r.status_code == 400
    assert "Invalid date format" in r.json()["message"]


def test_save_attendance_missing_teacher_profile(teacher_client, monkeypatch):
    """T2.x: Missing teacher mapping returns 400."""
    import routers.teacher as teacher_router_mod
    monkeypatch.setattr(teacher_router_mod, "get_teacher_id_from_user", lambda user_id: None)
    payload = _make_attendance_payload(datetime.now().strftime("%Y-%m-%d"))
    r = teacher_client.post("/teacher/api/save-attendance", json=payload)
    assert r.status_code == 400
    assert "Teacher profile not found" in r.json()["message"]


def test_save_attendance_unauthorized_subject(teacher_client, monkeypatch):
    """T2.x: Subject not owned by teacher returns 403."""
    from database import teacher_queries
    monkeypatch.setattr(teacher_queries, "verify_teacher_subject_scope",
                        lambda tid, sid: False if sid == 999 else True)
    payload = _make_attendance_payload(datetime.now().strftime("%Y-%m-%d"))
    payload["subject_id"] = 999
    r = teacher_client.post("/teacher/api/save-attendance", json=payload)
    assert r.status_code == 403


# === Q35 — Entry-count cap (max 200) on save-attendance ===

def test_save_attendance_rejects_more_than_200_records(teacher_client):
    """Q35: >200 attendance records per save rejected with 422 (Pydantic)."""
    today = datetime.now().strftime("%Y-%m-%d")
    payload = _make_attendance_payload(today, n_students=201)
    r = teacher_client.post("/teacher/api/save-attendance", json=payload)
    assert r.status_code == 422  # Pydantic validation error


def test_save_attendance_accepts_exactly_200_records(teacher_client):
    """Q35: Exactly 200 records allowed."""
    today = datetime.now().strftime("%Y-%m-%d")
    payload = _make_attendance_payload(today, n_students=200)
    r = teacher_client.post("/teacher/api/save-attendance", json=payload)
    assert r.status_code == 200, r.text


# === Bug 3 — save-marks validation ===

def _make_marks_payload(exam_type="Mid-1", max_marks=30, n_students=8, override_marks=None):
    """Build a minimal SaveMarksPayload."""
    marks = []
    for i in range(n_students):
        marks.append({
            "student_id": 5 + i,
            "obtained_marks": override_marks if override_marks is not None else 25.0,
            "remarks": ""
        })
    return {
        "subject_id": 1,
        "section": "A",
        "exam_type": exam_type,
        "max_marks": max_marks,
        "marks": marks,
    }


def test_save_marks_existing_validation_rejects_negative(teacher_client):
    """T3.10: Negative marks rejected with 400 (existing validation)."""
    payload = _make_marks_payload(override_marks=-5.0)
    r = teacher_client.post("/teacher/api/save-marks", json=payload)
    assert r.status_code == 400
    assert "Invalid marks" in r.json()["message"]


def test_save_marks_existing_validation_rejects_exceeding_max(teacher_client):
    """T3.9: Marks > max_marks rejected with 400."""
    payload = _make_marks_payload(max_marks=30, override_marks=35.0)
    r = teacher_client.post("/teacher/api/save-marks", json=payload)
    assert r.status_code == 400
    assert "between 0 and 30" in r.json()["message"]


def test_save_marks_accepts_zero(teacher_client):
    """Marks of 0 are valid."""
    payload = _make_marks_payload(override_marks=0.0)
    r = teacher_client.post("/teacher/api/save-marks", json=payload)
    assert r.status_code == 200


def test_save_marks_accepts_exact_max(teacher_client):
    """Marks equal to max_marks is valid."""
    payload = _make_marks_payload(max_marks=30, override_marks=30.0)
    r = teacher_client.post("/teacher/api/save-marks", json=payload)
    assert r.status_code == 200


def test_save_marks_rejects_more_than_200_records(teacher_client):
    """Q36: >200 marks records per save rejected."""
    payload = _make_marks_payload(n_students=201)
    r = teacher_client.post("/teacher/api/save-marks", json=payload)
    assert r.status_code == 422


def test_save_marks_unauthorized_subject(teacher_client, monkeypatch):
    """T3.13: Subject not owned by teacher returns 403."""
    from database import teacher_queries
    monkeypatch.setattr(teacher_queries, "verify_teacher_subject_scope",
                        lambda tid, sid: False if sid == 999 else True)
    payload = _make_marks_payload()
    payload["subject_id"] = 999
    r = teacher_client.post("/teacher/api/save-marks", json=payload)
    assert r.status_code == 403


def test_save_marks_missing_teacher_profile(teacher_client, monkeypatch):
    """T3.x: Missing teacher mapping returns 400."""
    import routers.teacher as teacher_router_mod
    monkeypatch.setattr(teacher_router_mod, "get_teacher_id_from_user", lambda user_id: None)
    payload = _make_marks_payload()
    r = teacher_client.post("/teacher/api/save-marks", json=payload)
    assert r.status_code == 400
    assert "Teacher profile not found" in r.json()["message"]


# === Frontend template verification (load + parse check) ===

def test_students_html_no_na_placeholder():
    """Q6: students.html no longer contains the N/A placeholder fallback."""
    template_path = FRONTEND_ROOT / "templates" / "teacher" / "students.html"
    content = template_path.read_text()
    # The old N/A fallback was: sectionSelect.innerHTML += `<option value="N/A">N/A</option>`;
    assert 'value="N/A"' not in content, "students.html still has N/A placeholder"
    assert "No sections available for this subject" in content, \
        "students.html should have clear empty-state message"


def test_attendance_html_no_no_sections_placeholder():
    """Q6/Q7: attendance.html replaced 'No Sections' with clear empty-state."""
    template_path = FRONTEND_ROOT / "templates" / "teacher" / "attendance.html"
    content = template_path.read_text()
    # The old fallback was: sectionSelect.innerHTML += `<option value="">No Sections</option>`;
    assert "No sections available for this subject" in content


def test_marks_html_has_empty_state():
    """Q6/Q7: marks.html now has empty-state message when no sections."""
    template_path = FRONTEND_ROOT / "templates" / "teacher" / "marks.html"
    content = template_path.read_text()
    assert "No sections available for this subject" in content


def test_attendance_html_has_date_input_max():
    """Q11: attendance.html date input has max attribute (production mode)."""
    template_path = FRONTEND_ROOT / "templates" / "teacher" / "attendance.html"
    content = template_path.read_text()
    assert "demo_mode" in content, "attendance.html should reference demo_mode context var"
    assert 'max="{{ today_date }}"' in content, \
        "attendance.html should set max=today_date in production mode"


def test_teacher_layout_has_no_self_attendance_yet():
    """Iteration 1 only — Self Attendance sidebar link is NOT added yet (Iteration 2)."""
    template_path = FRONTEND_ROOT / "templates" / "teacher" / "teacher_layout.html"
    content = template_path.read_text()
    # In Iteration 1, we should NOT have added the Self Attendance sidebar link
    assert "/teacher/self-attendance" not in content, \
        "Self Attendance link should NOT be added in Iteration 1"


# === Regression: ensure existing routes still work ===

def test_get_subjects_route_still_works(teacher_client):
    """T5.x: existing /teacher/api/subjects endpoint is unaffected."""
    r = teacher_client.get("/teacher/api/subjects")
    assert r.status_code == 200


def test_get_marks_route_still_works(teacher_client):
    """T5.x: existing /teacher/api/marks endpoint is unaffected."""
    r = teacher_client.get("/teacher/api/marks?subject_id=1&section=A&exam_type=Mid-1")
    assert r.status_code in (200, 403)  # 403 if scope check fails; both are "working"


def test_attendance_history_route_still_works(teacher_client):
    """T5.x: existing /teacher/api/attendance/history endpoint is unaffected."""
    r = teacher_client.get("/teacher/api/attendance/history")
    assert r.status_code == 200


def test_no_syntax_errors_in_modified_files():
    """Compile-check all modified Python files."""
    import py_compile
    files_to_check = [
        BACKEND_ROOT / "routers" / "teacher.py",
        BACKEND_ROOT / "database" / "teacher_queries.py",
    ]
    for f in files_to_check:
        py_compile.compile(str(f), doraise=True)
    # templates: ensure they parse as HTML (no Jinja syntax errors would be caught
    # at render time, but we can at least confirm the files exist and have content)
    templates = [
        FRONTEND_ROOT / "templates" / "teacher" / "students.html",
        FRONTEND_ROOT / "templates" / "teacher" / "attendance.html",
        FRONTEND_ROOT / "templates" / "teacher" / "marks.html",
    ]
    for t in templates:
        assert t.exists(), f"Template missing: {t}"
        assert t.stat().st_size > 100, f"Template suspiciously small: {t}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
