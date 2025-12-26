from io import BytesIO
from decimal import Decimal

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

from jobs.models import Job, JobRecord


# ----------------------------
# Helpers
# ----------------------------
def employee_display_name(emp):
    if not emp:
        return ""

    if getattr(emp, "preferred_name", None):
        return emp.preferred_name

    first = getattr(emp, "first_name", "") or ""
    last = getattr(emp, "last_name", "") or ""
    full = f"{first} {last}".strip()

    return full or emp.employee_email


# ----------------------------
# Receipt PDF
# ----------------------------
def job_receipt_pdf(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    buffer = BytesIO()

    # 58mm thermal
    receipt_width = 58 * mm
    receipt_height = 220 * mm

    doc = SimpleDocTemplate(
        buffer,
        pagesize=(receipt_width, receipt_height),
        rightMargin=6,
        leftMargin=6,
        topMargin=6,
        bottomMargin=6,
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="Brand",
        fontSize=11,
        alignment=1,
        spaceAfter=2,
        fontName="Helvetica-Bold",
    ))

    styles.add(ParagraphStyle(
        name="Muted",
        fontSize=7,
        alignment=1,
        textColor="#555555",
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        name="Section",
        fontSize=8,
        spaceBefore=6,
        spaceAfter=3,
        fontName="Helvetica-Bold",
    ))

    styles.add(ParagraphStyle(
        name="Body",
        fontSize=8,
        leading=10,
        spaceAfter=2,
    ))

    styles.add(ParagraphStyle(
        name="TotalLabel",
        fontSize=8,
        alignment=1,
        spaceAfter=2,
    ))

    styles.add(ParagraphStyle(
        name="TotalValue",
        fontSize=14,
        alignment=1,
        fontName="Helvetica-Bold",
        spaceAfter=8,
    ))

    elements = []

    # ----------------------------
    # Logo (optional)
    # ----------------------------
    logo_path = getattr(settings, "RECEIPT_LOGO_PATH", None)
    if logo_path:
        try:
            elements.append(Image(logo_path, width=28 * mm, height=18 * mm))
            elements.append(Spacer(1, 4))
        except Exception:
            pass

    # ----------------------------
    # Header
    # ----------------------------
    elements.append(Paragraph("FARHAT PRINTING PRESS", styles["Brand"]))
    elements.append(Paragraph("Official Receipt", styles["Muted"]))

    # ----------------------------
    # TOTAL BLOCK (hero)
    # ----------------------------
    elements.append(Paragraph("TOTAL", styles["TotalLabel"]))
    elements.append(
        Paragraph(f"GHS {job.total_amount}", styles["TotalValue"])
    )

    # ----------------------------
    # Meta
    # ----------------------------
    elements.append(Paragraph(
        f"Receipt #{job.pk}", styles["Body"]
    ))
    elements.append(Paragraph(
        timezone.now().strftime("%d %b %Y • %H:%M"),
        styles["Body"]
    ))

    elements.append(Spacer(1, 6))

    # ----------------------------
    # Customer
    # ----------------------------
    elements.append(Paragraph("Customer", styles["Section"]))
    elements.append(Paragraph(job.customer_name or "Walk-in", styles["Body"]))
    if job.customer_phone:
        elements.append(Paragraph(job.customer_phone, styles["Body"]))

    # ----------------------------
    # Services
    # ----------------------------
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("Services", styles["Section"]))

    records = JobRecord.objects.filter(job=job)

    if records.exists():
        for r in records:
            elements.append(
                Paragraph(
                    f"{job.service.name} × {r.quantity_produced}",
                    styles["Body"]
                )
            )
    else:
        elements.append(
            Paragraph(
                f"{job.service.name} × {job.quantity}",
                styles["Body"]
            )
        )

    # ----------------------------
    # Branch & Attendant
    # ----------------------------
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("Processed By", styles["Section"]))

    elements.append(Paragraph(job.branch.name, styles["Body"]))

    if job.created_by:
        elements.append(
            Paragraph(
                employee_display_name(job.created_by),
                styles["Body"]
            )
        )

    # ----------------------------
    # QR Code
    # ----------------------------
    elements.append(Spacer(1, 8))

    qr_data = f"JOB:{job.pk}|BRANCH:{job.branch.pk}"
    qr_widget = qr.QrCodeWidget(qr_data)
    bounds = qr_widget.getBounds()
    w = bounds[2] - bounds[0]
    h = bounds[3] - bounds[1]

    d = Drawing(32, 32, transform=[32.0 / w, 0, 0, 32.0 / h, 0, 0])
    d.add(qr_widget)

    elements.append(d)

    # ----------------------------
    # Footer
    # ----------------------------
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("Thank you 🙏", styles["Muted"]))
    elements.append(Paragraph("Please come again", styles["Muted"]))

    doc.build(elements)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="receipt_{job.pk}.pdf"'
    return response
