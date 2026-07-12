"""PDF Report Renderer: converts a validated ReportData contract into a
professional PDF document using ReportLab Platypus.

This module performs no database access, no service calls, and no AI
calls. It operates only on the immutable ReportData object and a
destination file path.
"""

from pathlib import Path

from reportlab.lib.units import inch
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
)

from app.reporting import templates
from app.schemas.report import (
    FindingDetail,
    RemediationGuidance,
    ReportData,
    SeverityDistribution,
)


def render_pdf(report_data: ReportData, output_path: Path) -> None:
    """Render the complete PDF report to output_path.

    Raises whatever ReportLab raises on a genuine rendering failure; the
    caller (ReportService) is responsible for translating that failure and
    cleaning up any partial output file.
    """
    styles = templates.get_styles()
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=templates.PAGE_SIZE,
        leftMargin=templates.MARGIN,
        rightMargin=templates.MARGIN,
        topMargin=templates.MARGIN,
        bottomMargin=templates.MARGIN,
        title="AVAP Vulnerability Assessment Report",
    )

    story: list = []
    story.extend(_build_cover(report_data, styles))
    story.append(PageBreak())
    story.extend(_build_executive_summary(report_data, styles))
    story.extend(_build_asset_overview(report_data, styles))
    story.append(PageBreak())
    story.extend(_build_findings(report_data, styles))

    doc.build(
        story, onFirstPage=templates.page_footer, onLaterPages=templates.page_footer
    )


def _build_cover(report_data: ReportData, styles: dict) -> list:
    meta = report_data.metadata
    return [
        Spacer(1, 1.4 * inch),
        Paragraph("AVAP Vulnerability Assessment Report", styles["Title"]),
        Spacer(1, 0.4 * inch),
        templates.metadata_table(
            [
                ("Target", meta.target),
                ("Target Type", meta.target_type.value),
                ("Scan Status", meta.scan_status.value),
                ("Report Generated", meta.generated_at.strftime("%Y-%m-%d %H:%M UTC")),
                ("Risk Calculation Version", meta.risk_calculation_version),
                ("Report Template Version", meta.report_template_version),
            ],
            styles,
        ),
    ]


def _build_executive_summary(report_data: ReportData, styles: dict) -> list:
    summary = report_data.executive_summary
    elements = [
        templates.heading("Executive Summary", 1, styles),
        templates.metadata_table(
            [
                ("Overall Risk Score", f"{summary.overall_risk_score:.1f} / 10.0"),
                ("Overall Risk Level", summary.overall_risk_level.value),
                ("Assets Assessed", str(summary.total_assets)),
                ("Vulnerabilities Found", str(summary.total_vulnerabilities)),
            ],
            styles,
        ),
        Spacer(1, 0.15 * inch),
        templates.heading("Severity Distribution", 2, styles),
        _severity_table(summary.severity_distribution),
        Spacer(1, 0.1 * inch),
    ]
    return elements


def _severity_table(distribution: SeverityDistribution) -> Table:
    header = ["Critical", "High", "Medium", "Low", "Informational"]
    values = [
        str(distribution.critical),
        str(distribution.high),
        str(distribution.medium),
        str(distribution.low),
        str(distribution.informational),
    ]
    table = Table([header, values], colWidths=[1.06 * inch] * 5)
    table.setStyle(templates.standard_table_style())
    return table


def _build_asset_overview(report_data: ReportData, styles: dict) -> list:
    elements = [templates.heading("Asset Overview", 1, styles)]
    if not report_data.assets:
        elements.append(
            templates.body_text("No assets were associated with this scan.", styles)
        )
        return elements

    rows = [["IP Address", "Hostname", "Operating System", "Risk Level", "Findings"]]
    for asset in report_data.assets:
        rows.append(
            [
                templates.safe_text(asset.ipv4),
                templates.safe_text(asset.hostname or "-"),
                templates.safe_text(asset.operating_system or "-"),
                asset.risk_level.value,
                str(asset.vulnerability_count),
            ]
        )
    table = Table(
        rows,
        colWidths=[1.1 * inch, 1.5 * inch, 1.7 * inch, 1.0 * inch, 0.8 * inch],
        repeatRows=1,
    )
    table.setStyle(templates.standard_table_style())
    elements.append(table)
    return elements


def _build_findings(report_data: ReportData, styles: dict) -> list:
    elements = [templates.heading("Detailed Findings", 1, styles)]
    for index, finding in enumerate(report_data.findings, start=1):
        elements.extend(_build_finding_section(index, finding, styles))
    return elements


def _build_finding_section(index: int, finding: FindingDetail, styles: dict) -> list:
    title = f"{index}. {finding.vulnerability_name}"
    if finding.cve:
        title += f" ({finding.cve})"
    elements = [templates.heading(title, 2, styles)]

    asset_label = finding.asset_ipv4
    if finding.asset_hostname:
        asset_label += f" ({finding.asset_hostname})"

    meta_rows = [
        ("Asset", asset_label),
        ("Severity Rating", finding.severity_rating),
        ("CVSS / Severity Score", f"{finding.severity_score:.1f}"),
        ("Deterministic Risk Score", f"{finding.risk_score:.1f} / 10.0"),
        ("Risk Level", finding.risk_level.value),
    ]
    if finding.affected_service:
        meta_rows.append(("Affected Service", _service_label(finding.affected_service)))

    elements.append(templates.metadata_table(meta_rows, styles))

    if finding.description:
        elements.append(Spacer(1, 0.05 * inch))
        elements.append(templates.body_text(finding.description, styles))

    if finding.remediation:
        elements.extend(_build_remediation(finding.remediation, styles))
    else:
        elements.append(Spacer(1, 0.05 * inch))
        elements.append(
            Paragraph(
                "<i>AI-assisted remediation guidance is not currently available "
                "for this finding.</i>",
                styles["Meta"],
            )
        )

    elements.append(Spacer(1, 0.15 * inch))
    return elements


def _service_label(service) -> str:
    label = f"{service.port}/{service.protocol} ({service.service_name})"
    if service.product:
        label += f" - {service.product}"
        if service.version:
            label += f" {service.version}"
    return label


def _build_remediation(remediation: RemediationGuidance, styles: dict) -> list:
    elements = [
        Spacer(1, 0.08 * inch),
        Paragraph("<b>AI-Assisted Remediation Guidance (Advisory)</b>", styles["Body"]),
        templates.body_text(remediation.summary, styles),
        templates.body_text(remediation.explanation, styles),
    ]
    elements.extend(
        _labeled_bullet_list("Remediation Steps", remediation.remediation_steps, styles)
    )
    elements.extend(
        _labeled_bullet_list("Validation Steps", remediation.validation_steps, styles)
    )
    elements.extend(_labeled_bullet_list("Cautions", remediation.cautions, styles))
    provider_label = templates.safe_text(remediation.provider)
    model_label = templates.safe_text(remediation.model)
    elements.append(
        Paragraph(
            f"<i>Advisory content generated by {provider_label} ({model_label})</i>",
            styles["Small"],
        )
    )
    return elements


def _labeled_bullet_list(label: str, items: list[str], styles: dict) -> list:
    if not items:
        return []
    return [
        templates.body_text(f"{label}:", styles),
        ListFlowable(
            [ListItem(templates.body_text(item, styles)) for item in items],
            bulletType="bullet",
        ),
    ]
