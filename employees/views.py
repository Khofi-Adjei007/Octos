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
from django.utils.http import url_has_allowed_host_and_scheme

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
@never_cache
def employeesLogin(request):
    """
    Login view with robust role detection and redirect:
      - if next param present and safe -> redirect(next)
      - else if superuser -> admin:index
      - else if branch manager -> branch_manager_dashboard
      - else if HR regional -> human_resources
      - else if role ATTENDANT -> attendant_dashboard
      - else if role CASHIER -> cashier_dashboard
      - else -> employeeHomepage
    """
    if request.method == "POST":
        form = EmployeeLoginForm(request.POST, request=request)
        if form.is_valid():
            identifier = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=identifier, password=password)

            if user is not None:
                login(request, user)
                logger.info(f"User {identifier} logged in successfully")

                # 1) safe 'next' handling (if you want to honour it)
                next_url = request.POST.get("next") or request.GET.get("next")
                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                    logger.info(f"Redirecting to next: {next_url}")
                    return redirect(next_url)

                # 2) superuser
                if user.is_superuser:
                    return redirect('admin:index')

                # 3) try to fetch a profile/employee object and determine role reliably
                profile = None
                role_obj = None

                # common related attributes to try
                related_names = ["userprofile", "employee", "profile"]
                for name in related_names:
                    try:
                        profile = getattr(user, name, None)
                        if profile is not None:
                            break
                    except Exception:
                        profile = None

                # if still not found, attempt direct Employee lookup (FK in employees app)
                if profile is None:
                    try:
                        from employees.models import Employee
                        profile = Employee.objects.filter(user=user).first()
                    except Exception:
                        profile = None

                # get role object if available
                try:
                    if profile and hasattr(profile, "role"):
                        role_obj = profile.role
                except Exception:
                    role_obj = None

                # fallback: role directly on user model
                if role_obj is None:
                    try:
                        if hasattr(user, "role"):
                            role_obj = getattr(user, "role")
                    except Exception:
                        role_obj = None

                role_code = ""
                try:
                    if role_obj and getattr(role_obj, "code", None):
                        role_code = getattr(role_obj, "code").upper()
                    elif role_obj and getattr(role_obj, "name", None):
                        role_code = getattr(role_obj, "name").upper()
                except Exception:
                    role_code = ""

                # 4) Branch manager
                try:
                    if profile and getattr(profile, "managed_branch", None) is not None:
                        return redirect('branch_manager_dashboard')
                except Exception:
                    logger.debug("Error checking managed_branch")

                # 5) HR check (regional)
                try:
                    if user.is_staff and profile and getattr(profile, "role", None) and profile.role.name == 'regional_hr_manager':
                        return redirect('human_resources')
                except Exception:
                    logger.debug("Error checking HR role")

                # 6) Role-based redirects (Attendant first)
                if role_code == "ATTENDANT":
                    return redirect('attendant_dashboard')   # -> /api/jobs/ui/attendant/
                if role_code == "CASHIER":
                    return redirect('cashier_dashboard')

                # 7) default
                return redirect("employeeHomepage")

            else:
                logger.warning(f"Failed login attempt for identifier {identifier}")

    else:
        form = EmployeeLoginForm()

    return render(request, "employeesLogin.html", {"form": form})



def employee_logout(request):
    logout(request)
    return redirect('employeesLogin')


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