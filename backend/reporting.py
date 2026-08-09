import io
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from .models import PredictionRecord

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

def generate_csv_report(db: Session) -> str:
    records = db.query(PredictionRecord).order_by(PredictionRecord.timestamp.desc()).limit(100).all()
    if not records:
        return "timestamp,species,final_classification,pollution_index,ml_prediction\n"

    data = []
    for r in records:
        data.append({
            "timestamp": r.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "species": r.species,
            "final_classification": r.final_classification,
            "pollution_index": r.pollution_index,
            "ml_prediction": r.ml_prediction,
            "anomaly_flag": r.anomaly_flag,
            "anomaly_score": r.anomaly_score
        })

    df = pd.DataFrame(data)
    return df.to_csv(index=False)

def generate_pdf_report(db: Session, pond_name: str = "Pond A", species: str = "Shrimp") -> bytes:
    if not HAS_REPORTLAB:
        # Fallback text if ReportLab unavailable
        return b"AquaSentinel+ Executive Summary Report (Install reportlab for PDF layout)"

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0284c7'),
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748b')
    )
    h2_style = ParagraphStyle(
        'H2Style',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#0f172a'),
        fontName='Helvetica-Bold'
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )

    story = []

    # Title Header
    story.append(Paragraph("AquaSentinel+ | Water Quality Intelligence Report", title_style))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Target: {pond_name} ({species})", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0'), spaceAfter=15))

    # Executive Summary Card
    latest = db.query(PredictionRecord).order_by(PredictionRecord.timestamp.desc()).first()
    pi_score = latest.pollution_index if latest else 12.4
    status = latest.final_classification if latest else "SAFE"
    ml_pred = latest.ml_prediction if latest else "Random Forest"

    story.append(Paragraph("Executive Summary & Risk Assessment", h2_style))
    story.append(Spacer(1, 6))

    summary_data = [
        [Paragraph("<b>Pond Identifier</b>", body_style), Paragraph(pond_name, body_style), Paragraph("<b>Target Species</b>", body_style), Paragraph(species, body_style)],
        [Paragraph("<b>Pollution Index</b>", body_style), Paragraph(f"{pi_score}/100", body_style), Paragraph("<b>Overall Status</b>", body_style), Paragraph(f"<b>{status}</b>", body_style)],
        [Paragraph("<b>ML Prediction</b>", body_style), Paragraph(ml_pred, body_style), Paragraph("<b>Anomaly Flag</b>", body_style), Paragraph("Normal Pattern" if not (latest and latest.anomaly_flag) else "ANOMALY DETECTED", body_style)]
    ]
    t = Table(summary_data, colWidths=[110, 150, 110, 150])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BORDER', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))

    # Decision Support Recommendations
    story.append(Paragraph("Actionable Decision Support Recommendations", h2_style))
    story.append(Spacer(1, 6))

    recs = [
        f"• Maintain continuous paddlewheel aeration during night hours for optimal DO in {species} ponds.",
        "• Perform bi-weekly water exchange (10-15% volume) to manage organic load.",
        "• Monitor pH diurnal fluctuations (keep variation within < 0.5 pH units per day)."
    ]
    for r in recs:
        story.append(Paragraph(r, body_style))
        story.append(Spacer(1, 3))

    story.append(Spacer(1, 15))

    # Recent Audit Log Table
    story.append(Paragraph("Recent Telemetry Audit Log (Last 5 Readings)", h2_style))
    story.append(Spacer(1, 6))

    recent = db.query(PredictionRecord).order_by(PredictionRecord.timestamp.desc()).limit(5).all()
    audit_rows = [["Time", "Species", "Pollution Index", "ML Status", "Final Classification"]]
    for rec in recent:
        audit_rows.append([
            rec.timestamp.strftime("%H:%M:%S"),
            rec.species,
            f"{rec.pollution_index:.1f}",
            rec.ml_prediction,
            rec.final_classification
        ])

    if len(audit_rows) == 1:
        audit_rows.append(["--:--:--", species, f"{pi_score}", ml_pred, status])

    audit_table = Table(audit_rows, colWidths=[90, 100, 100, 110, 120])
    audit_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0284c7')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(audit_table)

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceAfter=10))
    story.append(Paragraph("AquaSentinel+ AI Water Quality Intelligence System | Confidential Farm Operational Audit", subtitle_style))

    doc.build(story)
    return buffer.getvalue()
