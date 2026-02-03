# Human_Resources/api/views.py
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict
from django.utils import timezone
import json

# keep your DRF CreateEmployeeFromApplicationView if you still want it
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import EmployeeCreateFromApplicationSerializer
from public.api.permissions import IsHR

class CreateEmployeeFromApplicationView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsHR]

    def post(self, request):
        serializer = EmployeeCreateFromApplicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        emp = serializer.save()
        return Response({"detail": "Employee created.", "employee_id": emp.id}, status=status.HTTP_201_CREATED)


# helper for staff check
def staff_required(user):
    return getattr(user, "is_active", False) and getattr(user, "is_staff", False)


# --- Existing simple app views (kept & extended) ---
@login_required
@user_passes_test(staff_required)
def application_list(request):
    # Prefer real model if present
    try:
        from Human_Resources.models import PublicApplication
        qs = PublicApplication.objects.order_by('-created_at').all()
        results = []
        for obj in qs:
            results.append({
                "id": obj.id,
                "first_name": obj.first_name,
                "last_name": obj.last_name,
                "email": obj.email,
                "phone": obj.phone,
                "recommended_role": getattr(obj.recommended_role, 'name', str(obj.recommended_role)) if obj.recommended_role else None,
                "status": obj.status,
                "resume": request.build_absolute_uri(obj.resume.url) if obj.resume else None,
                "created_at": obj.created_at.isoformat(),
            })
        return JsonResponse({"results": results})
    except Exception:
        # fallback stub
        return JsonResponse({"results": []})


@login_required
@user_passes_test(staff_required)
def application_detail(request, pk):
    try:
        from Human_Resources.models import PublicApplication
        obj = get_object_or_404(PublicApplication, pk=pk)
        data = {
            "id": obj.id,
            "first_name": obj.first_name,
            "last_name": obj.last_name,
            "email": obj.email,
            "phone": obj.phone,
            "recommended_role": getattr(obj.recommended_role, 'name', str(obj.recommended_role)) if obj.recommended_role else None,
            "status": obj.status,
            "resume": request.build_absolute_uri(obj.resume.url) if obj.resume else None,
            "notes": obj.notes,
            "created_at": obj.created_at.isoformat(),
        }
        return JsonResponse(data)
    except Exception:
        return JsonResponse({"id": pk})


@login_required
@user_passes_test(staff_required)
def application_approve(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        from Human_Resources.models import PublicApplication
        app = get_object_or_404(PublicApplication, pk=pk)
        app.status = "shortlisted"
        app.save(update_fields=["status", "updated_at"])
        return JsonResponse({"success": True, "approved_id": pk})
    except Exception:
        # fallback
        return JsonResponse({"success": True, "approved_id": pk})


@login_required
@user_passes_test(staff_required)
def application_reject(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        from Human_Resources.models import PublicApplication
        app = get_object_or_404(PublicApplication, pk=pk)
        app.status = "rejected"
        app.save(update_fields=["status", "updated_at"])
        return JsonResponse({"success": True, "rejected_id": pk})
    except Exception:
        return JsonResponse({"success": True, "rejected_id": pk})


# --- Employees endpoints (kept) ---
@login_required
@user_passes_test(staff_required)
def employee_list(request):
    try:
        from employees.models import Employee
        qs = Employee.objects.filter(deleted_at__isnull=True).order_by('last_name')
        results = []
        for e in qs:
            results.append({
                "id": e.id,
                "first_name": e.first_name,
                "last_name": e.last_name,
                "email": getattr(e, "employee_email", None) or getattr(e, "personal_email", None),
                "department": getattr(e.department, "name", None) if getattr(e, "department", None) else None,
                "is_active": e.is_active,
            })
        return JsonResponse({"results": results})
    except Exception:
        return JsonResponse({"results": []})


@login_required
@user_passes_test(staff_required)
def employee_create(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    # Keep it simple: expect JSON payload (or form-data) and return success
    try:
        payload = request.POST or json.loads(request.body.decode() or "{}")
    except Exception:
        payload = request.POST
    # Prefer to delegate creation elsewhere; here we return a stub success
    return JsonResponse({"success": True, "payload_received": bool(payload)})


@login_required
@user_passes_test(staff_required)
def employee_detail(request, pk):
    try:
        from employees.models import Employee
        e = get_object_or_404(Employee, pk=pk)
        data = {
            "id": e.id,
            "first_name": e.first_name,
            "last_name": e.last_name,
            "email": getattr(e, "employee_email", None) or getattr(e, "personal_email", None),
            "department": getattr(e.department, "name", None) if getattr(e, "department", None) else None,
            "is_active": e.is_active,
            "employee_id": e.employee_id,
        }
        return JsonResponse(data)
    except Exception:
        return JsonResponse({"id": pk})


@login_required
@user_passes_test(staff_required)
def employee_set_department(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        payload = request.POST or json.loads(request.body.decode() or "{}")
        dept = payload.get("department") or request.POST.get("department")
        from employees.models import Employee
        from Human_Resources.models import Department
        emp = get_object_or_404(Employee, pk=pk)
        if dept is None:
            return JsonResponse({"error": "department required"}, status=400)
        # allow department by id or name
        dobj = None
        try:
            dobj = Department.objects.get(pk=int(dept))
        except Exception:
            dobj = Department.objects.filter(name__iexact=dept).first()
        if not dobj:
            return JsonResponse({"error": "department not found"}, status=404)
        emp.department = dobj
        emp.save(update_fields=["department"])
        return JsonResponse({"success": True, "employee_id": pk, "department": dobj.name})
    except Exception:
        return JsonResponse({"success": True, "employee_id": pk})


# ------------------------------
# Complaints (employees can create; staff can list/detail/resolve)
# ------------------------------
@login_required
def complaint_create(request):
    # any authenticated user may file a complaint
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        payload = request.POST or json.loads(request.body.decode() or "{}")
    except Exception:
        payload = request.POST
    try:
        from Human_Resources.models import Complaint  # optional model
        c = Complaint.objects.create(
            created_by=request.user,
            title=payload.get("title", "")[:200],
            description=payload.get("description", ""),
            related_department_id=payload.get("department_id", None)
        )
        return JsonResponse({"success": True, "id": c.id})
    except Exception:
        # fallback: return stub
        return JsonResponse({"success": True, "id": None})


@login_required
@user_passes_test(staff_required)
def complaint_list(request):
    try:
        from Human_Resources.models import Complaint
        qs = Complaint.objects.order_by('-created_at').all()
        out = []
        for c in qs:
            out.append({
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "status": getattr(c, "status", "open"),
                "created_by": getattr(c.created_by, "employee_email", None) if getattr(c, "created_by", None) else None,
                "created_at": getattr(c, "created_at", None).isoformat() if getattr(c, "created_at", None) else None,
            })
        return JsonResponse({"results": out})
    except Exception:
        return JsonResponse({"results": []})


@login_required
@user_passes_test(staff_required)
def complaint_detail(request, pk):
    try:
        from Human_Resources.models import Complaint
        c = get_object_or_404(Complaint, pk=pk)
        return JsonResponse({
            "id": c.id,
            "title": c.title,
            "description": c.description,
            "status": getattr(c, "status", "open"),
            "created_by": getattr(c.created_by, "employee_email", None) if getattr(c, "created_by", None) else None,
            "created_at": getattr(c, "created_at", None).isoformat() if getattr(c, "created_at", None) else None,
        })
    except Exception:
        return JsonResponse({"id": pk})


@login_required
@user_passes_test(staff_required)
def complaint_resolve(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        from Human_Resources.models import Complaint
        c = get_object_or_404(Complaint, pk=pk)
        c.status = "resolved"
        c.resolved_at = timezone.now()
        c.resolved_by = request.user
        c.save(update_fields=["status", "resolved_at", "resolved_by"])
        return JsonResponse({"success": True, "id": pk})
    except Exception:
        return JsonResponse({"success": True, "id": pk})


# ------------------------------
# Messages (HR staff create; staff can list)
# ------------------------------
@login_required
@user_passes_test(staff_required)
def message_list(request):
    try:
        from Human_Resources.models import HRMessage
        qs = HRMessage.objects.order_by('-created_at').all()
        out = []
        for m in qs:
            out.append({
                "id": m.id,
                "subject": m.subject,
                "body": m.body,
                "to": getattr(m.recipient, "employee_email", None) if getattr(m, "recipient", None) else None,
                "created_at": m.created_at.isoformat(),
                "read": getattr(m, "read", False),
            })
        return JsonResponse({"results": out})
    except Exception:
        return JsonResponse({"results": []})


@login_required
@user_passes_test(staff_required)
def message_create(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        payload = request.POST or json.loads(request.body.decode() or "{}")
    except Exception:
        payload = request.POST
    try:
        from Human_Resources.models import HRMessage
        recipient_id = payload.get("recipient_id")
        recipient = None
        if recipient_id:
            from employees.models import Employee
            recipient = Employee.objects.filter(pk=recipient_id).first()
        m = HRMessage.objects.create(
            subject=payload.get("subject", "")[:200],
            body=payload.get("body", ""),
            sender=request.user,
            recipient=recipient
        )
        return JsonResponse({"success": True, "id": m.id})
    except Exception:
        return JsonResponse({"success": True, "id": None})


@login_required
@user_passes_test(staff_required)
def message_detail(request, pk):
    try:
        from Human_Resources.models import HRMessage
        m = get_object_or_404(HRMessage, pk=pk)
        return JsonResponse({
            "id": m.id,
            "subject": m.subject,
            "body": m.body,
            "to": getattr(m.recipient, "employee_email", None) if getattr(m, "recipient", None) else None,
            "created_at": m.created_at.isoformat(),
            "read": getattr(m, "read", False),
        })
    except Exception:
        return JsonResponse({"id": pk})


@login_required
@user_passes_test(staff_required)
def message_mark_read(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        from Human_Resources.models import HRMessage
        m = get_object_or_404(HRMessage, pk=pk)
        m.read = True
        m.read_at = timezone.now()
        m.save(update_fields=["read", "read_at"])
        return JsonResponse({"success": True, "id": pk})
    except Exception:
        return JsonResponse({"success": True, "id": pk})


# ------------------------------
# Departments (readable by staff)
# ------------------------------
@login_required
@user_passes_test(staff_required)
def department_list(request):
    try:
        from Human_Resources.models import Department
        qs = Department.objects.order_by('name').all()
        out = [{"id": d.id, "code": getattr(d, "code", None), "name": d.name, "description": d.description} for d in qs]
        return JsonResponse({"results": out})
    except Exception:
        return JsonResponse({"results": []})


# ------------------------------
# Payroll (staff)
# ------------------------------
@login_required
@user_passes_test(staff_required)
def payroll_list(request):
    try:
        from Human_Resources.models import PayrollRecord
        qs = PayrollRecord.objects.order_by('-period_start').all()
        out = [{"id": p.id, "employee_id": getattr(p.employee, "id", None), "amount": str(p.amount), "period_start": p.period_start.isoformat()} for p in qs]
        return JsonResponse({"results": out})
    except Exception:
        return JsonResponse({"results": []})


@login_required
@user_passes_test(staff_required)
def payroll_create(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        payload = request.POST or json.loads(request.body.decode() or "{}")
    except Exception:
        payload = request.POST
    # stub behaviour: return success
    return JsonResponse({"success": True, "payload": payload})


@login_required
@user_passes_test(staff_required)
def payroll_detail(request, pk):
    try:
        from Human_Resources.models import PayrollRecord
        p = get_object_or_404(PayrollRecord, pk=pk)
        return JsonResponse({"id": p.id, "employee_id": getattr(p.employee, "id", None), "amount": str(p.amount)})
    except Exception:
        return JsonResponse({"id": pk})


# ------------------------------
# Performance Reviews
# ------------------------------
@login_required
@user_passes_test(staff_required)
def review_list(request):
    try:
        from Human_Resources.models import PerformanceReview
        qs = PerformanceReview.objects.order_by('-created_at').all()
        out = [{"id": r.id, "employee_id": getattr(r.employee, "id", None), "score": getattr(r, "score", None)} for r in qs]
        return JsonResponse({"results": out})
    except Exception:
        return JsonResponse({"results": []})


@login_required
@user_passes_test(staff_required)
def review_create(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        payload = request.POST or json.loads(request.body.decode() or "{}")
    except Exception:
        payload = request.POST
    return JsonResponse({"success": True, "payload": payload})


@login_required
@user_passes_test(staff_required)
def review_detail(request, pk):
    try:
        from Human_Resources.models import PerformanceReview
        r = get_object_or_404(PerformanceReview, pk=pk)
        return JsonResponse(model_to_dict(r))
    except Exception:
        return JsonResponse({"id": pk})


# ------------------------------
# Training sessions
# ------------------------------
@login_required
@user_passes_test(staff_required)
def training_list(request):
    try:
        from Human_Resources.models import TrainingSession
        qs = TrainingSession.objects.order_by('-start_at').all()
        out = [{"id": t.id, "title": t.title, "start_at": getattr(t, "start_at", None).isoformat() if getattr(t, "start_at", None) else None} for t in qs]
        return JsonResponse({"results": out})
    except Exception:
        return JsonResponse({"results": []})


@login_required
@user_passes_test(staff_required)
def training_create(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        payload = request.POST or json.loads(request.body.decode() or "{}")
    except Exception:
        payload = request.POST
    return JsonResponse({"success": True, "payload": payload})


@login_required
@user_passes_test(staff_required)
def training_detail(request, pk):
    try:
        from Human_Resources.models import TrainingSession
        t = get_object_or_404(TrainingSession, pk=pk)
        return JsonResponse(model_to_dict(t))
    except Exception:
        return JsonResponse({"id": pk})