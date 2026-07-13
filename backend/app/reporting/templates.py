"""Reusable ReportLab Platypus styles, components, and safe-text utilities
shared by the PDF renderer. Contains no business logic and no database
access.

`safe_text` is the single, centralized mechanism used to neutralize
untrusted persisted text (scanner-derived or AI-generated) before it
reaches a ReportLab `Paragraph`, which otherwise interprets a small
XML-like markup language in its input.
"""

from xml.sax.saxutils import (
    escape,  # nosec B406 -- output-escaping only, never parses XML
)

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Table, TableStyle

from app.core.enums import RiskLevel

PAGE_SIZE = letter
MARGIN = 0.75 * inch

_RISK_LEVEL_COLORS = {
    RiskLevel.CRITICAL: colors.HexColor("#7A0C0C"),
    RiskLevel.HIGH: colors.HexColor("#C0392B"),
    RiskLevel.MEDIUM: colors.HexColor("#D68910"),
    RiskLevel.LOW: colors.HexColor("#2E86C1"),
    RiskLevel.INFORMATIONAL: colors.HexColor("#566573"),
}

_HEADER_BG = colors.HexColor("#1B2631")
_ALT_ROW_BG = colors.HexColor("#F4F6F7")
_GRID_COLOR = colors.HexColor("#D5D8DC")
_MUTED_TEXT = colors.HexColor("#566573")


def safe_text(value: str | None) -> str:
    """Escape untrusted text so it can never be interpreted as ReportLab
    Paragraph markup. Every piece of scanner- or AI-derived text must pass
    through this function before being placed inside a Paragraph.
    """
    if not value:
        return ""
    return escape(str(value))


def risk_level_color(level: RiskLevel):
    """Return the accent color associated with a risk level."""
    return _RISK_LEVEL_COLORS.get(level, colors.black)


def get_styles() -> dict[str, ParagraphStyle]:
    """Build the AVAP report paragraph style set."""
    base = getSampleStyleSheet()
    return {
        "Title": ParagraphStyle(
            "AVAPTitle",
            parent=base["Title"],
            fontSize=22,
            spaceAfter=18,
            alignment=TA_CENTER,
            textColor=_HEADER_BG,
        ),
        "Heading1": ParagraphStyle(
            "AVAPHeading1",
            parent=base["Heading1"],
            fontSize=15,
            spaceBefore=16,
            spaceAfter=8,
            textColor=_HEADER_BG,
        ),
        "Heading2": ParagraphStyle(
            "AVAPHeading2",
            parent=base["Heading2"],
            fontSize=12,
            spaceBefore=10,
            spaceAfter=5,
            textColor=_HEADER_BG,
        ),
        "Body": ParagraphStyle(
            "AVAPBody",
            parent=base["Normal"],
            fontSize=9.5,
            leading=13,
            spaceAfter=5,
        ),
        "Meta": ParagraphStyle(
            "AVAPMeta",
            parent=base["Normal"],
            fontSize=9,
            leading=12,
            textColor=_MUTED_TEXT,
        ),
        "Small": ParagraphStyle(
            "AVAPSmall",
            parent=base["Normal"],
            fontSize=8,
            leading=11,
            textColor=_MUTED_TEXT,
        ),
    }


def heading(text: str, level: int, styles: dict) -> Paragraph:
    """A safely escaped section heading at the given level (1 or 2)."""
    style_key = "Heading1" if level == 1 else "Heading2"
    return Paragraph(safe_text(text), styles[style_key])


def body_text(text: str, styles: dict) -> Paragraph:
    """A safely escaped body paragraph."""
    return Paragraph(safe_text(text), styles["Body"])


def metadata_table(rows: list[tuple[str, str]], styles: dict) -> Table:
    """A two-column label/value table for metadata sections. Labels are
    trusted static strings; values are always escaped.
    """
    data = [
        [
            Paragraph(f"<b>{safe_text(label)}</b>", styles["Meta"]),
            Paragraph(safe_text(value), styles["Meta"]),
        ]
        for label, value in rows
    ]
    table = Table(data, colWidths=[1.9 * inch, 4.1 * inch])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def standard_table_style() -> TableStyle:
    """The shared visual style for header-row data tables (asset overview,
    severity distribution)."""
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.5, _GRID_COLOR),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _ALT_ROW_BG]),
        ]
    )


def page_footer(canvas, doc) -> None:
    """Stable footer applied to every page: platform label and page number."""
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(_MUTED_TEXT)
    canvas.drawString(
        MARGIN, 0.5 * inch, "AVAP - Automated Vulnerability Assessment Platform"
    )
    canvas.drawRightString(PAGE_SIZE[0] - MARGIN, 0.5 * inch, f"Page {doc.page}")
    canvas.line(MARGIN, 0.58 * inch, PAGE_SIZE[0] - MARGIN, 0.58 * inch)
    canvas.restoreState()
