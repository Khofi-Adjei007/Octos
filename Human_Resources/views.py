import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from employees.models import Employee
from services.services import EmployeeService
from Human_Resources.models import HiringRecommendation

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


# Human_Resources/views.py
from django.shortcuts import render, redirect
from employees.models import Employee

def branch_manager_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('employeesLogin')

    try:
        profile = request.user.userprofile
        if profile.managed_branch is None:
            return redirect('employeesLogin')  # No branch assigned
        branch = profile.managed_branch
    except request.user.userprofile.DoesNotExist:
        return redirect('employeesLogin')  # No UserProfile

    # Fetch employees for the branch
    employees = Employee.objects.filter(branch=branch)
    total_employees = employees.filter(is_active=True).count()
    pending_employees = employees.filter(is_active=False)

    # Mock data for tasks (since Task model isn't created yet)
    tasks_completed = 0
    tasks_pending = 0

    # Mock data for production status (since Production model isn't created yet)
    production_status = "N/A"

    # Mock data for inventory (since Inventory model isn't created yet)
    inventory = []

    # Mock data for metrics (since Production and Inventory models aren't created yet)
    productivity_rate = "N/A"
    equipment_utilization = "N/A"

    # Mock data for notifications (since Notification model isn't created yet)
    notifications = []

    # Context data for the template
    context = {
        'user': request.user,
        'tasks_completed': tasks_completed,
        'tasks_pending': tasks_pending,
        'production_status': production_status,
        'employees': employees,
        'inventory': inventory,
        'total_employees': total_employees,
        'productivity_rate': productivity_rate,
        'equipment_utilization': equipment_utilization,
        'pending_employees': pending_employees,
        'notifications': notifications,
    }

    return render(request, 'branch_manager_dashboard.html', context)