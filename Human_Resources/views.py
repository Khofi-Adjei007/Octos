import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from employees.models import Employee
from services.services import EmployeeService

logger = logging.getLogger(__name__)

@login_required
def human_resource(request):
    if not request.user.is_staff:
        return redirect('employeesLogin')
    
    # Get pending employees
    pending_employees = Employee.objects.filter(is_active=False)
    total_pending = pending_employees.count()

    # Calculate average time to approve for approved employees
    approved_employees = Employee.objects.filter(is_active=True, approved_at__isnull=False)
    avg_days_to_approve = 0
    if approved_employees.exists():
        total_days = 0
        for employee in approved_employees:
            time_diff = employee.approved_at - employee.created_at
            total_days += time_diff.days
        avg_days_to_approve = round(total_days / approved_employees.count(), 1)

    context = {
        'user': request.user,
        'pending_employees': pending_employees,
        'total_pending': total_pending,
        'avg_days_to_approve': avg_days_to_approve,
    }
    return render(request, 'human_resource.html', context)

@csrf_exempt
@login_required
def generate_employee_id(request, employee_id):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    try:
        employee = get_object_or_404(Employee, id=employee_id)
        employee_service = EmployeeService()
        new_employee_id = employee_service.generate_employee_id(employee)
        return JsonResponse({'success': True, 'employee_id': new_employee_id})
    except Exception as e:
        logger.error(f"Error generating employee ID for {employee_id}: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@login_required
def approve_employee(request, employee_id):
    logger.info(f"Received approve request for employee_id: {employee_id}")
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        employee = get_object_or_404(Employee, id=employee_id)
        data = {
            'employee_id': request.POST.get('employee_id'),
            'position': request.POST.get('position'),
            'hire_date': request.POST.get('hire_date'),
            'salary': request.POST.get('salary'),
            'work_schedule': request.POST.get('work_schedule'),
            'contract_type': request.POST.get('contract_type'),
            'equipment_assigned': request.POST.get('equipment_assigned'),
            'equipment_other': request.POST.get('equipment_other'),
        }
        for key, value in data.items():
            if value:
                setattr(employee, key, value)
        employee.is_active = True
        employee.status = 'active'
        employee.save()
        logger.info(f"Successfully approved employee {employee_id}")

        # Send SMS using EmployeeService
        employee_service = EmployeeService()
        sms_sent = employee_service.send_approval_sms(employee)
        if not sms_sent:
            logger.warning(f"SMS notification failed for employee {employee_id}, but approval was successful")

        # Always return success for the approval, even if SMS fails
        return JsonResponse({'success': True})
    logger.error(f"Invalid request method for employee_id: {employee_id}")
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)