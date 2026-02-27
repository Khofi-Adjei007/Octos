# employees/api.py

import io
import base64
import qrcode
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from employees.models import Employee
from Human_Resources.models.authority import AuthorityAssignment


@login_required
def employee_id_card_api(request, pk=None):
    """
    Returns all data needed to render the digital ID card.
    If pk is None, returns the logged-in user's card.
    """
    if pk:
        try:
            employee = Employee.objects.select_related(
                'branch', 'department', 'role'
            ).get(pk=pk)
        except Employee.DoesNotExist:
            return JsonResponse({"error": "Employee not found."}, status=404)
    else:
        employee = request.user

    # Get authority role
    assignment = (
        AuthorityAssignment.objects
        .filter(user=employee, is_active=True)
        .select_related('role')
        .first()
    )

    # Generate QR code as base64
    qr_data = f"FPP:{employee.employee_id}:{employee.employee_email}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1a1a1a", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    # Profile picture
    profile_pic_url = None
    if employee.profile_picture:
        try:
            profile_pic_url = employee.profile_picture.url
        except Exception:
            pass

    return JsonResponse({
        "id":             employee.pk,
        "employee_id":    employee.employee_id or "—",
        "first_name":     employee.first_name,
        "last_name":      employee.last_name,
        "full_name":      f"{employee.first_name} {employee.last_name}",
        "initials":       f"{employee.first_name[:1]}{employee.last_name[:1]}".upper(),
        "email":          employee.employee_email or "—",
        "phone":          employee.phone_number or "—",
        "position_title": employee.position_title or "—",
        "department":     employee.department.name if employee.department else "—",
        "branch":         employee.branch.name if employee.branch else "—",
        "authority_role": assignment.role.name if assignment and assignment.role else "—",
        "employment_type": employee.get_employee_type_display(),
        "employment_status": employee.get_employment_status_display(),
        "card_status":    employee.card_status,
        "profile_pic_url": profile_pic_url,
        "qr_code":        qr_base64,
    })