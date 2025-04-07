# employees/views.py
from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from django.db import IntegrityError
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .employeeForms import EmployeeLoginForm, EmployeeRegistrationForm
from .models import Employee
import logging
from Human_Resources.models import UserProfile

logger = logging.getLogger(__name__)

@never_cache
def employeeregistration(request):
    if request.method == 'POST':
        form = EmployeeRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('employeesLogin')
    else:
        form = EmployeeRegistrationForm()
    return render(request, 'employeeregistration.html', {'form': form})

@never_cache
def employeesLogin(request):
    if request.method == "POST":
        form = EmployeeLoginForm(request.POST, request=request)
        if form.is_valid():
            email = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                logger.info(f"User {email} logged in successfully")

                # Superuser check
                if user.is_superuser:
                    logger.info(f"Redirecting superuser {email} to admin:index")
                    return redirect('admin:index')

                # Check for UserProfile
                try:
                    profile = user.userprofile

                    # Branch Manager check
                    if profile.managed_branch is not None:
                        logger.info(f"User {email} is a branch manager for branch {profile.managed_branch.name}. Redirecting to branch_manager_dashboard")
                        return redirect('branch_manager_dashboard')

                    # HR check
                    if user.is_staff and profile.role and profile.role.name == 'regional_hr_manager':
                        logger.info(f"Redirecting HR user {email} to human_resources")
                        return redirect('human_resources')

                except UserProfile.DoesNotExist:
                    logger.warning(f"User {email} has no UserProfile")

                # Default redirect for regular employees
                logger.info(f"Redirecting employee {email} to employeeHomepage")
                return redirect("employeeHomepage")

            else:
                logger.warning(f"Failed login attempt for email {email}")
    else:
        form = EmployeeLoginForm()
    return render(request, "employeesLogin.html", {"form": form})

def employee_logout(request):
    logout(request)
    return redirect('employeesLogin')

# Employees Homepage Redirect
@never_cache
@login_required
def employeeHomepage(request):
    try:
        employee = Employee.objects.get(employee_email=request.user.employee_email)
    except Employee.DoesNotExist:
        logout(request)
        return redirect('employeesLogin')
    
    context = {
        'employee': employee,
        'status_message': 'Your application has been approved!' if employee.is_active else 'Your application is pending approval.'
    }
    return render(request, 'employeesHomepage.html', context)