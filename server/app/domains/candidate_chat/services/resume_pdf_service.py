"""
Resume PDF generation and storage.

- Builds a PDF from structured resume_data (reportlab).
- Uploads to Supabase storage when configured; returns public URL for download.
"""

from io import BytesIO
from typing import Any, Dict, Optional
from uuid import UUID

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.config.settings import get_settings
from app.shared.logging import get_logger

logger = get_logger(__name__)

# Section display order and titles for PDF
SECTION_TITLES: Dict[str, str] = {
    "personal_info": "Personal Information",
    "qualifications": "Qualifications",
    "skills": "Skills",
    "education": "Education",
    "experience": "Experience",
    "job_preferences": "Job Preferences",
    "portfolio": "Portfolio",
    "about": "About",
    "additional_info": "Additional Information",
}


def _format_value(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "Yes" if v else "No"
    if isinstance(v, list):
        return ", ".join(str(x) for x in v)
    return str(v).strip()


def build_resume_pdf(resume_data: dict) -> bytes:
    """
    Generate a PDF from structured resume_data (meta + sections).

    Returns:
        PDF file as bytes.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="ResumeTitle",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=6,
    )
    heading_style = ParagraphStyle(
        name="SectionHeading",
        parent=styles["Heading2"],
        fontSize=12,
        spaceBefore=12,
        spaceAfter=6,
    )
    meta = resume_data.get("meta", {})
    raw_role = (meta.get("role_name") or "").strip()
    role_name = raw_role if raw_role and raw_role.lower() != "unknown" else ""
    sections = resume_data.get("sections", {})

    # Title: full name + role (only show role when set and not "Unknown")
    personal = sections.get("personal_info", {})
    full_name = personal.get("full_name", "Resume")
    title_text = full_name
    if role_name:
        title_text += f" — {role_name}"

    flow: list = [Paragraph(title_text, title_style), Spacer(1, 0.2 * inch)]

    for section_key, section_title in SECTION_TITLES.items():
        section_data = sections.get(section_key)
        if not section_data:
            continue

        flow.append(Paragraph(section_title, heading_style))

        rows = []
        for k, v in section_data.items():
            if v is None or (isinstance(v, str) and not v.strip()):
                continue
            label = k.replace("_", " ").title()
            value = _format_value(v)
            if not value:
                continue
            rows.append([label, value])

        if rows:
            t = Table(rows, colWidths=[2.2 * inch, 4.3 * inch])
            t.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 2),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )
            flow.append(t)
            flow.append(Spacer(1, 0.1 * inch))

    doc.build(flow)
    buffer.seek(0)
    return buffer.getvalue()


def upload_resume_pdf(
    pdf_bytes: bytes,
    candidate_id: UUID,
    version: int,
) -> Optional[str]:
    """
    Upload resume PDF to Supabase storage (if configured).
    Returns public URL for download, or None if upload skipped/failed.
    """
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        logger.debug("Supabase storage not configured; skipping resume PDF upload")
        return None

    try:
        from supabase import create_client

        client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key,
        )
        bucket = settings.supabase_resume_bucket
        path = f"{candidate_id}/resume_v{version}.pdf"

        # Bucket must exist (e.g. create "resumes" in Supabase Dashboard or via frontend)
        client.storage.from_(bucket).upload(
            path,
            pdf_bytes,
            file_options={"content-type": "application/pdf", "upsert": "true"},
        )
        # Public URL (if bucket is public)
        url = client.storage.from_(bucket).get_public_url(path)
        logger.info("Resume PDF uploaded", extra={"candidate_id": str(candidate_id), "path": path})
        return url
    except Exception as e:
        logger.exception("Resume PDF upload failed: %s", e)
        return None
