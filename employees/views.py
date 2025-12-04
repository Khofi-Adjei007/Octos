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
from .utils.employee_login import EmployeeLogin



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
    if request.method == "POST":
        form = EmployeeLoginForm(request.POST, request=request)
        if form.is_valid():
            identifier = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            user = authenticate(request, username=identifier, password=password)

            if user is not None:
                login(request, user)
                logger.info("User %s logged in successfully", identifier)

                # 1) safe 'next' handling (view-level)
                next_url = request.POST.get("next") or request.GET.get("next")
                if next_url and url_has_allowed_host_and_scheme(
                    next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure()
                ):
                    logger.info("Redirecting to next: %s", next_url)
                    return redirect(next_url)

                # 2) delegate decision to helper
                decision = EmployeeLogin(request, user).resolve_redirect()

                if decision:
                    try:
                        if decision.get("type") == "named":
                            return redirect(decision["name"], **(decision.get("kwargs") or {}))
                        elif decision.get("type") == "url":
                            return redirect(decision["url"])
                    except Exception as exc:
                        logger.exception("Error executing redirect decision %s: %s", decision, exc)

                # fallback default (safety)
                return redirect("employeeHomepage")

            else:
                logger.warning("Failed login attempt for identifier %s", identifier)
                messages.error(request, "Invalid credentials")
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