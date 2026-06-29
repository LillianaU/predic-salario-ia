"""
Generador de PDF para informes de Pertinencia Laboral.

Utiliza reportlab para generar documentos PDF profesionales con
formato azul (tema del proyecto), metadata del programa académico,
contenido del informe Groq y pie de página con copyright.

Author: Lilliana Uribe González
Version: 2.0
"""

from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY


def generate_pertinencia_pdf(
    program_name: str,
    occupation_name: str,
    cno_code: str,
    cuoc_code: str,
    report_text: str,
    created_at: str,
    author: str = "Lilliana Uribe González",
) -> bytes:
    """Generate a PDF report for Pertinencia Laboral.

    Args:
        program_name: Name of the academic program.
        occupation_name: Target occupation.
        cno_code: CNO code.
        cuoc_code: CUOC code.
        report_text: The generated report text (Groq output).
        created_at: Timestamp string.
        author: Report author.

    Returns:
        PDF file bytes.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()

    blue_dark = HexColor("#0A1F50")
    blue_primary = HexColor("#4A90E2")
    blue_light = HexColor("#B0C4DE")
    white = HexColor("#FFFFFF")
    gray = HexColor("#666666")

    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=22,
        textColor=blue_dark,
        spaceAfter=6,
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=gray,
        alignment=TA_CENTER,
        spaceAfter=20,
    )
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=blue_dark,
        spaceBefore=16,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=HexColor("#333333"),
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    )
    label_style = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=9,
        textColor=gray,
    )
    value_style = ParagraphStyle(
        "Value",
        parent=styles["Normal"],
        fontSize=10,
        textColor=HexColor("#333333"),
        fontName="Helvetica-Bold",
    )

    elements = []

    # Header
    elements.append(Paragraph("Informe de Pertinencia Laboral", title_style))
    elements.append(
        Paragraph(
            "PredicSalario IA — Sistema de Análisis Laboral TIC",
            subtitle_style,
        )
    )
    elements.append(
        HRFlowable(width="100%", thickness=2, color=blue_primary, spaceAfter=12)
    )

    # Metadata table
    meta_data = [
        ["Programa Académico:", program_name],
        ["Ocupación Objetivo:", occupation_name],
        ["Código CNO:", cno_code],
        ["Código CUOC:", cuoc_code],
        ["Fecha de Generación:", created_at],
        ["Generado por:", f"PredicSalario IA — {author}"],
    ]
    meta_table = Table(meta_data, colWidths=[2 * inch, 4.5 * inch])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), HexColor("#F0F4F8")),
                ("TEXTCOLOR", (0, 0), (0, -1), gray),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                ("ALIGN", (1, 0), (1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, blue_light),
            ]
        )
    )
    elements.append(meta_table)
    elements.append(Spacer(1, 16))

    # Report content
    elements.append(
        HRFlowable(width="100%", thickness=1, color=blue_light, spaceAfter=8)
    )
    elements.append(Paragraph("Análisis de Pertinencia", heading_style))

    # Parse report text into paragraphs
    for line in report_text.split("\n"):
        line = line.strip()
        if not line:
            elements.append(Spacer(1, 6))
            continue
        if line.startswith("#"):
            clean = line.lstrip("#").strip()
            elements.append(Paragraph(clean, heading_style))
        elif line.startswith("**") and line.endswith("**"):
            clean = line.strip("*").strip()
            elements.append(Paragraph(f"<b>{clean}</b>", body_style))
        elif line.startswith("- ") or line.startswith("• "):
            clean = line.lstrip("-• ").strip()
            elements.append(Paragraph(f"• {clean}", body_style))
        else:
            elements.append(Paragraph(line, body_style))

    # Footer
    elements.append(Spacer(1, 24))
    elements.append(
        HRFlowable(width="100%", thickness=1, color=blue_light, spaceAfter=8)
    )
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=gray,
        alignment=TA_CENTER,
    )
    elements.append(
        Paragraph(
            f"© 2025 {author} — PredicSalario IA — Todos los derechos reservados",
            footer_style,
        )
    )
    elements.append(
        Paragraph(
            "Generado automáticamente por el Sistema de Análisis Laboral TIC — Junio 2025",
            footer_style,
        )
    )

    doc.build(elements)
    return buffer.getvalue()
