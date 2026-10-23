# utils/pdf_generator.py
import io
import os
import re
import abc
from xml.sax.saxutils import escape as _xml_escape

import qrcode
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
from reportlab.lib.pagesizes import A5
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    HRFlowable, ListFlowable, KeepTogether,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.lib.fonts import addMapping

# === DejaVu Sans font registration (Unicode-safe, embedded) ===
# DejaVuSans-Oblique.ttf is NOT installed on this system; we register the
# available variants (Normal + Bold) and synthesize italic/boldItalic via
# ReportLab's addMapping so <i> and <b><i> tags do not crash.
_FONT_DIR_DEJAVU = "/usr/share/fonts/truetype/dejavu"
_DEJAVU_REGISTERED = False
try:
    if os.path.exists(os.path.join(_FONT_DIR_DEJAVU, "DejaVuSans.ttf")):
        pdfmetrics.registerFont(TTFont("DejaVuSans", os.path.join(_FONT_DIR_DEJAVU, "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", os.path.join(_FONT_DIR_DEJAVU, "DejaVuSans-Bold.ttf")))
        registerFontFamily(
            "DejaVuSans",
            normal="DejaVuSans",
            bold="DejaVuSans-Bold",
            italic="DejaVuSans",            # fallback to normal (synthetic slant)
            boldItalic="DejaVuSans-Bold",   # fallback to bold
        )
        # Synthetic italic mappings so <i>...</i> works without the .ttf file
        addMapping("DejaVuSans", 0, 0, "DejaVuSans")         # normal -> normal
        addMapping("DejaVuSans", 1, 0, "DejaVuSans-Bold")    # bold -> bold
        addMapping("DejaVuSans", 0, 1, "DejaVuSans")          # italic -> normal (synthetic)
        addMapping("DejaVuSans", 1, 1, "DejaVuSans-Bold")    # boldItalic -> bold (synthetic)
        _DEJAVU_REGISTERED = True
except Exception as _e:
    import sys
    print(f"Warning: DejaVu font registration failed ({_e}); falling back to Helvetica.", file=sys.stderr)
    _DEJAVU_REGISTERED = False


# === Resume Builder styles (DejaVu Sans, A4, 10pt body) ===
_BASE_FONT = "DejaVuSans" if _DEJAVU_REGISTERED else "Helvetica"
_BASE_FONT_BOLD = "DejaVuSans-Bold" if _DEJAVU_REGISTERED else "Helvetica-Bold"

STYLE_RESUME_NAME = ParagraphStyle(
    "ResumeName",
    fontName=_BASE_FONT_BOLD, fontSize=20, alignment=1,  # centered, 20pt (was 22)
    spaceAfter=2, leading=22,
)
STYLE_RESUME_CONTACT = ParagraphStyle(
    "ResumeContact",
    fontName=_BASE_FONT, fontSize=8, alignment=1, leading=10, spaceAfter=2,
)
STYLE_RESUME_SECTION = ParagraphStyle(
    "ResumeSection",
    fontName=_BASE_FONT_BOLD, fontSize=11, spaceAfter=1, spaceBefore=2, leading=13,
)
STYLE_RESUME_BODY = ParagraphStyle(
    "ResumeBody",
    fontName=_BASE_FONT, fontSize=10, leading=11, spaceAfter=1,
)
STYLE_RESUME_BULLET = ParagraphStyle(
    "ResumeBullet",
    fontName=_BASE_FONT, fontSize=10, leading=11,
    leftIndent=10, bulletIndent=0, spaceAfter=0,
)
STYLE_RESUME_LEFT = ParagraphStyle(
    "ResumeLeft",
    fontName=_BASE_FONT, fontSize=10, leading=11, alignment=0,
)
STYLE_RESUME_RIGHT = ParagraphStyle(
    "ResumeRight",
    fontName=_BASE_FONT, fontSize=10, leading=11, alignment=2,
)
STYLE_RESUME_BOLD_LEFT = ParagraphStyle(
    "ResumeBoldLeft",
    fontName=_BASE_FONT_BOLD, fontSize=10, leading=11, alignment=0,
)
STYLE_RESUME_ITALIC = ParagraphStyle(
    "ResumeItalic",
    fontName=_BASE_FONT, fontSize=10, leading=11,
)


# === Safe text helpers (blueprint §6.2.2) ===
def _safe(text):
    """Escape user-provided text for ReportLab Paragraph mini-HTML.

    Converts & < > " to their entity equivalents, preventing the
    `AI & Machine Learning` -> `AI &MachineLearning;` entity-interpolation
    bug observed in the legacy generator.
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    return _xml_escape(text, {'"': "&quot;"})


def _safe_url(url):
    """Escape a URL for use in a Paragraph <a href="..."> attribute."""
    if url is None:
        return ""
    return _xml_escape(str(url), {'"': "&quot;"})


def _strip_scheme(url):
    """Remove http:// or https:// for display text."""
    if not url:
        return ""
    s = str(url)
    if s.startswith("https://"):
        return s[8:]
    if s.startswith("http://"):
        return s[7:]
    return s


# === Engine-agnostic renderer adapter (blueprint §4.1) ===
class ResumeRenderer(abc.ABC):
    """Abstract interface for resume PDF rendering.

    Concrete implementations:
      - ReportLabResumeRenderer (default, ships now)
      - LatexResumeRenderer (stub only in this iteration)
    """

    @abc.abstractmethod
    def render(self, resume_data: dict) -> io.BytesIO:
        """Render a v2 resume_data dict to a PDF BytesIO stream.

        Raises ResumeRenderError on failure.
        """
        raise NotImplementedError


class ResumeRenderError(Exception):
    """Sanitized error raised to the API layer.

    The original exception (if any) is logged server-side; only a generic
    message is exposed to the client via this class.
    """


def get_resume_renderer() -> ResumeRenderer:
    """Factory: selects renderer based on env var RESUME_RENDERER.

    Default: "reportlab". If "latex" is requested, attempts to import
    LatexResumeRenderer; if that raises NotImplementedError (stub) or
    ImportError, falls back to ReportLabResumeRenderer.
    """
    engine = os.getenv("RESUME_RENDERER", "reportlab").lower()
    if engine == "latex":
        try:
            from utils.latex_renderer import LatexResumeRenderer
            return LatexResumeRenderer()
        except (ImportError, NotImplementedError):
            return ReportLabResumeRenderer()
    return ReportLabResumeRenderer()


# === ReportLab implementation (blueprint §4.2, §5, §8.6) ===
class ReportLabResumeRenderer(ResumeRenderer):
    """ReportLab-based resume renderer matching the target PDF layout.

    Page geometry (verified from Dnish_resume.pdf via pdftotext -bbox-layout):
      - A4 (595.276 x 841.89 pt)
      - Left/right margin: 46.8 pt (~0.65 inch)
      - Top margin: 25.2 pt (~0.35 inch)
      - Bottom margin: 46.8 pt
    """

    PAGE_SIZE = A4
    LEFT_MARGIN = 46.8
    RIGHT_MARGIN = 46.8
    TOP_MARGIN = 20.0
    BOTTOM_MARGIN = 30.0

    # Two-column entry widths.
    # Text region = 595.276 - 46.8*2 = 501.676 pt ~ 6.95 inch.
    # Split as 3.8 inch (left) + 2.5 inch (right); fits with slack.
    LEFT_COL_WIDTH = 3.8 * inch
    RIGHT_COL_WIDTH = 2.5 * inch

    def render(self, resume_data: dict) -> io.BytesIO:
        """Render a v2 resume_data dict to a PDF BytesIO."""
        if not isinstance(resume_data, dict):
            raise ResumeRenderError("Resume data must be a dict")

        personal = resume_data.get("personal") or {}
        full_name = personal.get("full_name") or "Your Name"

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.PAGE_SIZE,
            leftMargin=self.LEFT_MARGIN,
            rightMargin=self.RIGHT_MARGIN,
            topMargin=self.TOP_MARGIN,
            bottomMargin=self.BOTTOM_MARGIN,
            title=f"{full_name} - Resume",
            author=full_name,
            creator="SGI Command Center Resume Builder",
            subject="",
        )
        elements = []

        # Header (always rendered)
        elements.extend(self._build_header(resume_data))

        # Sections in target order with empty-section omission (blueprint §3.4, §5.3)
        if (resume_data.get("summary") or "").strip():
            elements.extend(self._build_summary(resume_data["summary"]))

        if self._has_entries(resume_data.get("experience"), "title"):
            elements.extend(self._build_experience(resume_data.get("experience") or []))

        if self._has_entries(resume_data.get("projects"), "title"):
            elements.extend(self._build_projects(resume_data.get("projects") or []))

        if self._has_skills(resume_data.get("technical_skills")):
            elements.extend(self._build_skills(resume_data.get("technical_skills") or {}))

        if self._has_entries(resume_data.get("certifications"), "title"):
            elements.extend(self._build_certs(resume_data.get("certifications") or []))

        if self._has_entries(resume_data.get("education"), "degree"):
            elements.extend(self._build_education(resume_data.get("education") or []))

        try:
            doc.build(elements)
        except Exception as e:
            import sys
            print(f"ReportLab build error: {e}", file=sys.stderr)
            raise ResumeRenderError("PDF build failed") from e

        buffer.seek(0)
        return buffer

    # === Section builders ===

    def _build_header(self, data):
        personal = data.get("personal") or {}
        elements = []
        name = (personal.get("full_name") or "Your Name").upper()
        elements.append(Paragraph(_safe(name), STYLE_RESUME_NAME))

        # Contact line: email | linkedin | phone | location | github | portfolio
        parts = []
        if personal.get("email"):
            email_url = f"mailto:{_safe_url(personal['email'])}"
            parts.append(f'<a href="{email_url}">{_safe(personal["email"])}</a>')
        if personal.get("linkedin"):
            label = _strip_scheme(personal["linkedin"])
            parts.append(
                f'<a href="{_safe_url(personal["linkedin"])}" color="blue">{_safe(label)}</a>'
            )
        if personal.get("phone"):
            parts.append(_safe(personal["phone"]))
        if personal.get("location"):
            parts.append(_safe(personal["location"]))
        if personal.get("github"):
            label = _strip_scheme(personal["github"])
            parts.append(
                f'<a href="{_safe_url(personal["github"])}" color="blue">{_safe(label)}</a>'
            )
        if personal.get("portfolio"):
            label = _strip_scheme(personal["portfolio"])
            parts.append(
                f'<a href="{_safe_url(personal["portfolio"])}" color="blue">{_safe(label)}</a>'
            )
        if parts:
            elements.append(Paragraph(" | ".join(parts), STYLE_RESUME_CONTACT))
        elements.append(Spacer(1, 6))
        return elements

    def _section_heading(self, title):
        """Section heading + horizontal rule (blueprint §5.4)."""
        return [
            Paragraph(_safe(title), STYLE_RESUME_SECTION),
            HRFlowable(
                width="100%", thickness=0.5, color=colors.black,
                spaceBefore=1, spaceAfter=4,
            ),
        ]

    def _build_summary(self, summary):
        elements = self._section_heading("Summary")
        for line in summary.split("\n"):
            if line.strip():
                elements.append(Paragraph(_safe(line), STYLE_RESUME_BODY))
        elements.append(Spacer(1, 3))
        return elements

    def _build_experience(self, experiences):
        elements = self._section_heading("Work Experience")
        for exp in experiences:
            if not exp.get("title"):
                continue
            left_parts = [_safe(exp.get("title") or "")]
            if exp.get("organization"):
                left_parts.append("\u2013")  # en-dash
                left_parts.append(_safe(exp["organization"]))
            left_text = " ".join(left_parts)
            right_text = self._format_date_range(
                exp.get("start_date"), exp.get("end_date")
            )
            row_table = Table(
                [[Paragraph(left_text, STYLE_RESUME_BOLD_LEFT),
                  Paragraph(_safe(right_text), STYLE_RESUME_RIGHT)]],
                colWidths=[self.LEFT_COL_WIDTH, self.RIGHT_COL_WIDTH],
            )
            row_table.setStyle(TableStyle([
                ("LEFTPADDING", (0,0), (-1,-1), 0),
                ("RIGHTPADDING", (0,0), (-1,-1), 0),
                ("TOPPADDING", (0,0), (-1,-1), 0),
                ("BOTTOMPADDING", (0,0), (-1,-1), 2),
                ("VALIGN", (0,0), (-1,-1), "TOP"),
            ]))
            block = [row_table]
            if exp.get("location"):
                block.append(Paragraph(_safe(exp["location"]), STYLE_RESUME_BODY))
            bullets = [
                Paragraph(_safe(b), STYLE_RESUME_BULLET)
                for b in (exp.get("bullets") or []) if b
            ]
            if bullets:
                block.append(ListFlowable(
                    bullets, bulletType="bullet", start="\u2022",
                    leftIndent=10, bulletFontName=_BASE_FONT,
                    bulletFontSize=10,
                ))
            elements.append(KeepTogether(block))
            elements.append(Spacer(1, 3))
        return elements

    def _build_projects(self, projects):
        elements = self._section_heading("Projects")
        for proj in projects:
            if not proj.get("title"):
                continue
            left_text = _safe(proj["title"])
            right_text = _safe(proj.get("category") or "")
            row_table = Table(
                [[Paragraph(left_text, STYLE_RESUME_BOLD_LEFT),
                  Paragraph(right_text, STYLE_RESUME_RIGHT)]],
                colWidths=[self.LEFT_COL_WIDTH, self.RIGHT_COL_WIDTH],
            )
            row_table.setStyle(TableStyle([
                ("LEFTPADDING", (0,0), (-1,-1), 0),
                ("RIGHTPADDING", (0,0), (-1,-1), 0),
                ("TOPPADDING", (0,0), (-1,-1), 0),
                ("BOTTOMPADDING", (0,0), (-1,-1), 2),
                ("VALIGN", (0,0), (-1,-1), "TOP"),
            ]))
            block = [row_table]
            bullets = [
                Paragraph(_safe(b), STYLE_RESUME_BULLET)
                for b in (proj.get("bullets") or []) if b
            ]
            if bullets:
                block.append(ListFlowable(
                    bullets, bulletType="bullet", start="\u2022",
                    leftIndent=10, bulletFontName=_BASE_FONT,
                    bulletFontSize=10,
                ))
            elements.append(KeepTogether(block))
            elements.append(Spacer(1, 3))
        return elements

    def _build_skills(self, skills):
        elements = self._section_heading("Technical Skills")
        defaults = [
            "Languages", "AIML", "AI Frameworks", "AI APIs", "Computer Vision",
            "Libraries", "Frameworks", "Databases", "Analytics", "Tools",
        ]
        ordered = []
        for cat in defaults:
            vals = skills.get(cat)
            if isinstance(vals, list) and vals:
                ordered.append((cat, vals))
        for cat, vals in skills.items():
            if cat == "_custom" or cat in defaults:
                continue
            if isinstance(vals, list) and vals:
                ordered.append((cat, vals))
        custom = skills.get("_custom") or []
        if isinstance(custom, list):
            for c in custom:
                if isinstance(c, dict):
                    name = c.get("name")
                    vals = c.get("values") or []
                    if name and isinstance(vals, list) and vals:
                        ordered.append((name, vals))

        rows = []
        for cat, vals in ordered:
            label = Paragraph(f"<b>{_safe(cat)}:</b>", STYLE_RESUME_LEFT)
            value = Paragraph(
                ", ".join(_safe(v) for v in vals if v),
                STYLE_RESUME_LEFT,
            )
            rows.append([label, value])
        if not rows:
            return []
        skills_table = Table(
            rows,
            colWidths=[1.5 * inch, 5.45 * inch],
        )
        skills_table.setStyle(TableStyle([
            ("LEFTPADDING", (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 0),
            ("TOPPADDING", (0,0), (-1,-1), 1),
            ("BOTTOMPADDING", (0,0), (-1,-1), 1),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
        ]))
        elements.append(skills_table)
        elements.append(Spacer(1, 3))
        return elements

    def _build_certs(self, certs):
        elements = self._section_heading("Certifications")
        for cert in certs:
            if not cert.get("title"):
                continue
            left_text = _safe(cert["title"])
            right_text = self._format_date_range(
                cert.get("start_date"), cert.get("end_date")
            )
            row_table = Table(
                [[Paragraph(left_text, STYLE_RESUME_BOLD_LEFT),
                  Paragraph(_safe(right_text), STYLE_RESUME_RIGHT)]],
                colWidths=[self.LEFT_COL_WIDTH, self.RIGHT_COL_WIDTH],
            )
            row_table.setStyle(TableStyle([
                ("LEFTPADDING", (0,0), (-1,-1), 0),
                ("RIGHTPADDING", (0,0), (-1,-1), 0),
                ("TOPPADDING", (0,0), (-1,-1), 0),
                ("BOTTOMPADDING", (0,0), (-1,-1), 1),
                ("VALIGN", (0,0), (-1,-1), "TOP"),
            ]))
            block = [row_table]
            sub = []
            if cert.get("issuer"):
                sub.append(_safe(cert["issuer"]))
            if cert.get("location"):
                sub.append(_safe(cert["location"]))
            if sub:
                block.append(Paragraph(", ".join(sub), STYLE_RESUME_BODY))
            if cert.get("certificate_id"):
                block.append(
                    Paragraph(f"ID: {_safe(cert['certificate_id'])}", STYLE_RESUME_BODY)
                )
            if cert.get("url"):
                block.append(
                    Paragraph(
                        f'<a href="{_safe_url(cert["url"])}" color="blue">'
                        f'{_safe(_strip_scheme(cert["url"]))}</a>',
                        STYLE_RESUME_BODY,
                    )
                )
            elements.append(KeepTogether(block))
            elements.append(Spacer(1, 3))
        return elements

    def _build_education(self, educations):
        elements = self._section_heading("Education")
        for edu in educations:
            if not edu.get("degree"):
                continue
            right_text = self._format_date_range(
                edu.get("start_date"), edu.get("end_date")
            )
            t1 = Table(
                [[Paragraph(_safe(edu["degree"]), STYLE_RESUME_BOLD_LEFT),
                  Paragraph(_safe(right_text), STYLE_RESUME_RIGHT)]],
                colWidths=[self.LEFT_COL_WIDTH, self.RIGHT_COL_WIDTH],
            )
            t1.setStyle(TableStyle([
                ("LEFTPADDING", (0,0), (-1,-1), 0),
                ("RIGHTPADDING", (0,0), (-1,-1), 0),
                ("TOPPADDING", (0,0), (-1,-1), 0),
                ("BOTTOMPADDING", (0,0), (-1,-1), 1),
                ("VALIGN", (0,0), (-1,-1), "TOP"),
            ]))
            block = [t1]
            inst_parts = []
            if edu.get("institution"):
                inst_parts.append(_safe(edu["institution"]))
            if edu.get("location"):
                inst_parts.append(_safe(edu["location"]))
            score_text = ""
            if edu.get("score_label") and edu.get("score_value"):
                score_text = f"{_safe(edu['score_label'])}: {_safe(edu['score_value'])}"
            elif edu.get("score_value"):
                score_text = _safe(edu["score_value"])
            if inst_parts or score_text:
                t2 = Table(
                    [[Paragraph(", ".join(inst_parts), STYLE_RESUME_LEFT),
                      Paragraph(score_text, STYLE_RESUME_RIGHT)]],
                    colWidths=[self.LEFT_COL_WIDTH, self.RIGHT_COL_WIDTH],
                )
                t2.setStyle(TableStyle([
                    ("LEFTPADDING", (0,0), (-1,-1), 0),
                    ("RIGHTPADDING", (0,0), (-1,-1), 0),
                    ("TOPPADDING", (0,0), (-1,-1), 0),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 1),
                    ("VALIGN", (0,0), (-1,-1), "TOP"),
                ]))
                block.append(t2)
            if edu.get("affiliation"):
                block.append(Paragraph(_safe(edu["affiliation"]), STYLE_RESUME_BODY))
            elements.append(KeepTogether(block))
            elements.append(Spacer(1, 3))
        return elements

    # === Helpers ===

    def _format_date_range(self, start, end):
        s = _safe(start) if start else ""
        e = _safe(end) if end else ""
        if s and e:
            return f"{s} \u2013 {e}"
        if s:
            return s
        if e:
            return e
        return ""

    def _has_entries(self, items, required_field):
        if not isinstance(items, list):
            return False
        return any(
            isinstance(i, dict) and (i.get(required_field) or "").strip()
            for i in items
        )

    def _has_skills(self, skills):
        if not isinstance(skills, dict):
            return False
        for cat, vals in skills.items():
            if cat == "_custom":
                if isinstance(vals, list):
                    for c in vals:
                        if isinstance(c, dict) and c.get("values"):
                            return True
                continue
            if isinstance(vals, list) and vals:
                if any(v for v in vals):
                    return True
        return False


# === Legacy shim for backward compatibility (blueprint §8.6) ===
def generate_resume_pdf(resume_data):
    """DEPRECATED. Use get_resume_renderer().render(data) instead.

    Kept for any caller that has not migrated; the only caller in this
    codebase (routers/student.py) is updated to use get_resume_renderer().
    """
    return get_resume_renderer().render(resume_data)


# ============================================================
# Legacy generators below (unchanged, NOT modified by the
# Resume Builder enhancement): student list, attendance report,
# fee receipt, generic report, payslip, relieving letter,
# visitor pass, MoM.
# ============================================================

def generate_student_list_pdf(students):
    """Generates a professional PDF list of all students."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    styles = getSampleStyleSheet()
    elements = []

    # Header
    elements.append(Paragraph("<b>SGI Command Center</b>", styles['Title']))
    elements.append(Paragraph("Comprehensive Student List Report", styles['Heading2']))
    elements.append(Spacer(1, 0.2 * inch))

    # Table Data
    data = [["ID", "Name", "Email", "Department", "Sem", "CGPA"]]
    for s in students:
        data.append([
            str(s["student_id"]),
            Paragraph(s["full_name"], styles['Normal']),
            Paragraph(s["email"], styles['Normal']),
            Paragraph(s["department_name"] or "-", styles['Normal']),
            str(s["semester"]),
            str(s["cgpa"] or "-")
        ])

    # FIX: Adjusted column widths to fit perfectly within 7.5 inches (Standard Letter Page Width)
    table = Table(data, colWidths=[0.4*inch, 1.4*inch, 2.0*inch, 2.2*inch, 0.5*inch, 0.6*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey)
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_attendance_report_pdf(low_attendance_students):
    """Generates a PDF report of students with low attendance."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>SGI Command Center</b>", styles['Title']))
    elements.append(Paragraph("Low Attendance Warning Report (< 75%)", styles['Heading2']))
    elements.append(Spacer(1, 0.2 * inch))

    data = [["Student Name", "Subject", "Attendance %", "Shortage"]]
    for s in low_attendance_students:
        shortage = round(75 - float(s["percentage"]), 2)
        data.append([
            Paragraph(s["student_name"], styles['Normal']),
            Paragraph(s["subject_name"], styles['Normal']),
            f'{s["percentage"]}%',
            f'{shortage}%'
        ])

    table = Table(data, colWidths=[2.0*inch, 2.5*inch, 1.5*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc3545')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey)
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_fee_receipt_pdf(payment_data):
    """Generates a PDF fee receipt using ReportLab."""
    buffer = io.BytesIO()

    # A5 size is perfect for receipts
    doc = SimpleDocTemplate(buffer, pagesize=A5, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    styles = getSampleStyleSheet()
    elements = []

    # Header
    elements.append(Paragraph("<b>SGI Command Center</b>", styles['Title']))
    elements.append(Paragraph("Fee Payment Receipt", styles['Normal']))
    elements.append(Spacer(1, 10))

    # Receipt Details Table
    data = [
        ["Receipt No:", payment_data.get("receipt_number", "N/A")],
        ["Date:", payment_data.get("payment_date", "N/A")],
        ["Student Name:", payment_data.get("full_name", "N/A")],
        ["Enrollment No:", payment_data.get("enrollment_no", "N/A")],
        ["Department:", payment_data.get("department_name", "N/A")],
        ["Semester:", payment_data.get("semester", "N/A")],
        ["Payment Mode:", payment_data.get("payment_mode", "N/A")],
        ["Transaction ID:", payment_data.get("transaction_id", "N/A")],
        ["Amount Paid:", f"₹ {payment_data.get('amount_paid', 0):,.2f}"],
    ]

    t = Table(data, colWidths=[120, 180])
    t.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))

    # Footer
    elements.append(Paragraph("<i>This is a computer-generated receipt and does not require a physical signature.</i>",
                              styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_generic_report_pdf(report_title, columns, row_keys, rows):
    """Generates a professional PDF for any report dynamically."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    styles = getSampleStyleSheet()
    elements = []

    # Header
    elements.append(Paragraph("<b>SGI Command Center</b>", styles['Title']))
    elements.append(Paragraph(report_title, styles['Heading2']))
    elements.append(Spacer(1, 0.2 * inch))

    # Prepare Data
    data = [columns]  # Header Row
    for row in rows:
        row_data = [Paragraph(str(row.get(key, "-")), styles['Normal']) for key in row_keys]
        data.append(row_data)

    # Calculate Column Widths (Equal Distribution)
    num_cols = len(columns)
    col_width = 7.0 / num_cols * inch  # 7.0 inches is usable width on Letter

    table = Table(data, colWidths=[col_width] * num_cols)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey)
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_payslip_pdf(payslip_data):
    """Generates a professional PDF payslip."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A5, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    styles = getSampleStyleSheet()
    elements = []

    # Header
    elements.append(Paragraph("<b>SGI Command Center</b>", styles['Title']))
    elements.append(Paragraph("Monthly Payslip", styles['Normal']))
    elements.append(Spacer(1, 10))

    # Employee Info
    emp_info = [
        ["Employee Name:", payslip_data["full_name"]],
        ["Employee Code:", payslip_data["employee_code"]],
        ["Designation:", payslip_data["designation"]],
        ["Pay Period:", f"{payslip_data['month']}/{payslip_data['year']}"],
        ["Payable Days:", f"{payslip_data['payable_days']} / {payslip_data['calendar_days']}"],
    ]
    t1 = Table(emp_info, colWidths=[120, 180])
    t1.setStyle(
        TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.grey), ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey)]))
    elements.append(t1)
    elements.append(Spacer(1, 15))

    # Salary Breakdown
    data = [["Component", "Type", "Amount (₹)"]]
    for item in payslip_data["items"]:
        data.append([item["component_name"], item["component_type"], f"{item['amount']:.2f}"])

    data.append(["", "Gross Earnings:", f"{payslip_data['gross_earnings']:.2f}"])
    data.append(["", "Total Deductions:", f"{payslip_data['total_deductions']:.2f}"])
    data.append(["", "Net Payable:", f"{payslip_data['net_payable']:.2f}"])

    t2 = Table(data, colWidths=[120, 80, 100])
    t2.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -3), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
    ]))
    elements.append(t2)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("<i>This is a system-generated payslip and does not require a physical signature.</i>",
                              styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_relieving_letter_pdf(emp_data, exit_data):
    """Generates a relieving letter PDF."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=30)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>SGI Command Center</b>", styles['Title']))
    elements.append(Paragraph("Relieving Certificate", styles['Heading2']))
    elements.append(Spacer(1, 20))

    text = f"""
    This is to certify that <b>{emp_data['full_name']}</b> (Employee Code: {emp_data['employee_code']}),
    employed as <b>{emp_data['designation']}</b>, has been relieved from their duties with effect from
    <b>{exit_data['last_working_day']}</b>.<br/><br/>

    The employee has completed all necessary clearances and handed over all company assets and responsibilities.
    Full and final settlement has been processed.<br/><br/>

    We wish them success in their future endeavors.
    """
    elements.append(Paragraph(text, styles['Normal']))
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("Authorized Signatory", styles['Normal']))
    elements.append(Paragraph("SGI Command Center", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_visitor_pass_pdf(visitor_data):
    """Generates a printable visitor pass with QR Code."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A5, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    styles = getSampleStyleSheet()
    elements = []

    # Header
    elements.append(Paragraph("<b>SGI Command Center</b>", styles['Title']))
    elements.append(Paragraph("Visitor Entry Pass", styles['Heading2']))
    elements.append(Spacer(1, 10))

    # Visitor Details Table
    data = [
        ["Visitor Name:", visitor_data["full_name"]],
        ["Mobile:", visitor_data["mobile"]],
        ["Host:", visitor_data["host_name"]],
        ["Department:", visitor_data["department_name"] or "-"],
        ["Purpose:", visitor_data["purpose"]],
        ["Visit Date:", str(visitor_data["visit_date"])],
        ["Pass Reference:", visitor_data["qr_reference"]],
    ]

    t = Table(data, colWidths=[100, 200])
    t.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))

    # Generate QR Code for the pass
    qr_dir = "static/uploads/qrcodes"
    os.makedirs(qr_dir, exist_ok=True)
    qr_path = f"{qr_dir}/visitor_{visitor_data['qr_reference']}.png"

    if not os.path.exists(qr_path):
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(f"VISITOR:{visitor_data['qr_reference']}")
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(qr_path)

    # Add QR Code to PDF
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Scan at gate for verification:", styles['Normal']))
    elements.append(Spacer(1, 5))

    from reportlab.platypus import Image as RLImage
    img_obj = RLImage(qr_path, width=100, height=100)
    elements.append(img_obj)

    elements.append(Spacer(1, 15))
    elements.append(Paragraph(
        "<i>This pass is valid only for the specified visit date. Please return this pass at the gate during check-out.</i>",
        styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_mom_pdf(meeting_data):
    """Generates formal Minutes of Meeting PDF."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=30)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>SGI Command Center</b>", styles['Title']))
    elements.append(Paragraph("Minutes of Meeting", styles['Heading2']))
    elements.append(Spacer(1, 20))

    # Meeting Details
    data = [
        ["Meeting Title:", meeting_data["title"]],
        ["Date:", str(meeting_data["meeting_date"])],
        ["Venue:", meeting_data["venue"] or "N/A"],
        ["Chairperson:", meeting_data["chairperson_name"]],
        ["Organizer:", meeting_data["organizer_name"]],
        ["Department:", meeting_data["department_name"] or "Institution Wide"],
        ["Status:", meeting_data["status"]],
    ]
    t = Table(data, colWidths=[120, 200])
    t.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.grey), ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey)]))
    elements.append(t)
    elements.append(Spacer(1, 20))

    # Agenda
    elements.append(Paragraph("<b>Agenda</b>", styles['Heading3']))
    elements.append(Paragraph(meeting_data["agenda"] or "N/A", styles['Normal']))
    elements.append(Spacer(1, 15))

    # Minutes
    elements.append(Paragraph("<b>Minutes of Discussion</b>", styles['Heading3']))
    elements.append(Paragraph(meeting_data["minutes"] or "N/A", styles['Normal']))
    elements.append(Spacer(1, 40))

    # Signatories
    elements.append(Paragraph("Prepared By: " + meeting_data["organizer_name"], styles['Normal']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Approved By: " + meeting_data["chairperson_name"], styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer
