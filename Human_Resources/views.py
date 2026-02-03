# Human_Resources/views.py
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
from employees.models import Employee
from services.services import EmployeeService, MetricsService
from django.contrib import messages
from .RecommendationForm import RecommendationForm
from .models import AuditLog, Role
from hr_workflows.models import Recommendation, user_profile as UserProfile
from employees.employeeForms import EmployeeRegistrationForm
import datetime

logger = logging.getLogger(__name__)

#### Start HR Dashboard View ####
def hr_dashboard(request):
    return render(request, 'dashboard.html')

#### End HR Dashboard View ####
@login_required
def human_resource(request):
    if not request.user.is_staff:
        return redirect('employeesLogin')
    
    # Get pending employees
    pending_employees = Employee.objects.filter(is_active=False)
    total_pending = pending_employees.count()

    # Get pending recommendations
    pending_recommendations = Recommendation.objects.filter(status='pending')

    # Calculate metrics using MetricsService
    metrics_service = MetricsService()
    today = datetime.date.today()
    metrics = metrics_service.calculate_recruitment_metrics(date_filter='this_month', today=today)

    # Handle recommendation approval
    if request.method == 'POST' and 'approve_recommendation' in request.POST:
        recommendation_id = request.POST.get('recommendation_id')
        try:
            recommendation = Recommendation.objects.get(id=recommendation_id, status='pending')
            recommendation.status = 'approved'
            recommendation.save()

            # Generate the registration link
            registration_link = request.build_absolute_uri(
                reverse('complete_registration', args=[recommendation.token])
            )

            # Send the link via email using EmployeeService
            employee_service = EmployeeService()
            email_sent = employee_service.send_registration_link(
                email=recommendation.email,
                link=registration_link,
                first_name=recommendation.first_name,
                last_name=recommendation.last_name
            )

            if email_sent:
                # Log the action
                AuditLog.objects.create(
                    action='recommendation_approved',
                    user=request.user,
                    recommendation=recommendation,
                    details=f"Recommendation for {recommendation.first_name} {recommendation.last_name} approved by {request.user.employee_email}"
                )
                messages.success(request, f"Recommendation for {recommendation.first_name} {recommendation.last_name} approved. Registration link sent.")
            else:
                messages.error(request, f"Recommendation approved, but failed to send email to {recommendation.email}.")
        except Recommendation.DoesNotExist:
            messages.error(request, "Recommendation not found or already processed.")
        return redirect('human_resources')

    context = {
        'user': request.user,
        'pending_employees': pending_employees,
        'total_pending': total_pending,
        'metrics': metrics, 
        'pending_recommendations': pending_recommendations,
    }
    return render(request, 'hr/dashboard.html', context)

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

        # Map requested_role to department and is_staff
        if employee.requested_role:
            role_name = employee.requested_role.name
            if role_name == 'regional_hr_manager':
                employee.department = 'HR'
                employee.is_staff = True
            elif role_name == 'branch_manager':
                employee.department = 'MANAGEMENT'
            elif role_name in ['general_attendant', 'cashier', 'cleaner']:
                employee.department = 'OPERATIONS'
            elif role_name == 'graphic_designer':
                employee.department = 'MARKETING'
            elif role_name in ['marketer']:
                employee.department = 'SALES'
            elif role_name in ['zonal_delivery_dispatch_rider']:
                employee.department = 'DELIVERY'
            elif role_name in ['field_officer']:
                employee.department = 'OPERATIONS'
            elif role_name in ['secretary']:
                employee.department = 'MANAGEMENT'
            elif role_name in ['accountant']:
                employee.department = 'ACCOUNTING'
            elif role_name in ['it_support_technician']:
                employee.department = 'IT'
            elif role_name in ['inventory_manager']:
                employee.department = 'OPERATIONS'
            elif role_name in ['quality_control_inspector']:
                employee.department = 'QUALITY_CONTROL'

        # Set employee status
        employee.is_active = True
        employee.status = 'active'
        employee.save()
        logger.info(f"Successfully approved employee {employee_id}")

        # Create or update UserProfile
        profile, created = UserProfile.objects.get_or_create(user=employee)
        profile.role = employee.requested_role
        if employee.requested_role and employee.requested_role.name == 'branch_manager':
            profile.managed_branch = employee.branch  # Assuming branch is set
        profile.department = employee.department  # Sync with Employee.department
        profile.save()

        # Send SMS using EmployeeService
        employee_service = EmployeeService()
        sms_sent = employee_service.send_approval_sms(employee)
        if not sms_sent:
            logger.warning(f"SMS notification failed for employee {employee_id}, but approval was successful")

        # Always return success for the approval, even if SMS fails
        return JsonResponse({'success': True})
    
    logger.error(f"Invalid request method for employee_id: {employee_id}")
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

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

    # Create the RecommendationForm instance
    form = RecommendationForm(user=request.user)

    # Context data for the template
    context = {
        'user': request.user,
        'branch': branch,
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
        'form': form,  # Add the form to the context
    }

    return render(request, 'branch_manager_dashboard.html', context)

@login_required
def recommend_employee(request):
    # Restrict access to Branch Managers
    try:
        profile = request.user.userprofile
        if not profile.role or profile.role.name != 'branch_manager':
            messages.error(request, "Only Branch Managers can recommend employees.")
            return redirect('branch_manager_dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found. Please contact HR.")
        return redirect('employeesLogin')

    # Prepare dashboard context
    branch = profile.managed_branch
    employees = Employee.objects.filter(branch=branch)
    total_employees = employees.filter(is_active=True).count()
    pending_employees = employees.filter(is_active=False)
    tasks_completed = 0
    tasks_pending = 0
    production_status = "N/A"
    inventory = []
    productivity_rate = "N/A"
    equipment_utilization = "N/A"
    notifications = []

    if request.method == 'POST':
        form = RecommendationForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            # Check for duplicate recommendation by email
            email = form.cleaned_data['email']
            if Recommendation.objects.filter(email=email, status='pending').exists():
                messages.error(request, f"A pending recommendation already exists for {email}.")
            else:
                # Save the recommendation
                recommendation = form.save(commit=False)
                recommendation.created_by = request.user
                recommendation.status = 'pending'
                recommendation.save()

                # Fix: Use recommended_role directly as a string
                AuditLog.objects.create(
                    action='recommendation_created',
                    user=request.user,
                    recommendation=recommendation,
                    details=f"Recommendation created for {recommendation.first_name} {recommendation.last_name} (Role: {recommendation.recommended_role}) by {request.user.employee_email}"
                )

                messages.success(request, f"Recommendation for {recommendation.first_name} {recommendation.last_name} submitted successfully. HR will review it.")
                return redirect('branch_manager_dashboard')
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = RecommendationForm(user=request.user)

    # Render the dashboard template with the form
    context = {
        'user': request.user,
        'branch': branch,
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
        'form': form,
    }
    return render(request, 'branch_manager_dashboard.html', context)

def complete_registration(request, token):
    # Validate the token
    try:
        recommendation = Recommendation.objects.get(token=token, status='approved')
    except Recommendation.DoesNotExist:
        raise Http404("Invalid or expired registration link.")

    if request.method == 'POST':
        form = EmployeeRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            # Create the Employee record
            employee = form.save(commit=False)
            employee.employee_email = recommendation.email  # Ensure email matches recommendation
            employee.first_name = recommendation.first_name
            employee.last_name = recommendation.last_name
            employee.branch = recommendation.branch
            employee.requested_role = Role.objects.get(name=recommendation.recommended_role)
            employee.is_active = False  # Pending final HR approval
            employee.save()

            # Update the recommendation status
            recommendation.status = 'completed'
            recommendation.save()

            # Log the action
            AuditLog.objects.create(
                action='form_submitted',
                recommendation=recommendation,
                details=f"Registration form submitted for {employee.first_name} {employee.last_name} (Email: {employee.employee_email})"
            )

            messages.success(request, "Registration completed successfully. HR will review your application.")
            return redirect('employeesLogin')  # Redirect to login page
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        # Pre-fill the form with recommendation data
        initial_data = {
            'first_name': recommendation.first_name,
            'last_name': recommendation.last_name,
            'employee_email': recommendation.email,
            'branch': recommendation.branch,
        }
        form = EmployeeRegistrationForm(initial=initial_data)

    context = {
        'form': form,
        'recommendation': recommendation,
    }
    return render(request, 'complete_registration.html', context)