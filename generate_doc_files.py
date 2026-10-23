# generate_doc_files.py
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def create_dummy_pdfs():
    doc_dir = "private_uploads/docs"
    os.makedirs(doc_dir, exist_ok=True)
    styles = getSampleStyleSheet()

    files = ['policy_2024.pdf', 'aicte_2023.pdf']
    for f in files:
        path = os.path.join(doc_dir, f)
        if not os.path.exists(path):
            doc = SimpleDocTemplate(path, pagesize=A4)
            elements = [
                Paragraph("<b>SGI Command Center</b>", styles['Title']),
                Spacer(1, 20),
                Paragraph(f"This is a dummy document generated for testing: {f}", styles['Normal']),
                Spacer(1, 20),
                Paragraph(
                    "In a real production environment, this would be the actual institutional policy or approval letter.",
                    styles['Normal'])
            ]
            doc.build(elements)
            print(f"✅ Created: {path}")
        else:
            print(f"Already exists: {path}")


if __name__ == "__main__":
    create_dummy_pdfs()