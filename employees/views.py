"""
employees/views.py

Employee authentication and entry-point views.

Responsibilities:
- Employee registration
- Employee login & logout
- Post-login routing
"""

import logging

from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.contrib.auth import login, logout
from django.utils.http import url_has_allowed_host_and_scheme
from django.db import IntegrityError
from django.core.exceptions import PermissionDenied

from .models import Employee
from .employeeForms import EmployeeLoginForm, EmployeeRegistrationForm
from employees.auth.guards import require_employee_login
from employees.auth.permissions import employee_has_permission

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# Employee Registration
# -------------------------------------------------------------------
@never_cache
def employeeregistration(request):
    if request.method == "POST":
        form = EmployeeRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                form.save()
                return redirect("employeesLogin")
            except IntegrityError:
                messages.error(request, "An account with this information already exists.")
    else:
        form = EmployeeRegistrationForm()

    return render(request, "employeeregistration.html", {"form": form})


# -------------------------------------------------------------------
# Employee Login
# -------------------------------------------------------------------
@never_cache
def employeesLogin(request):
    if request.method == "POST":
        form = EmployeeLoginForm(request.POST, request=request)

        if form.is_valid():
            if form.user:
                login(request, form.user)
                logger.info("User %s logged in successfully", form.user.employee_email)

                # Superusers only — honour ?next=
                if form.user.is_superuser:
                    next_url = request.POST.get("next") or request.GET.get("next")
                    if next_url and url_has_allowed_host_and_scheme(
                        next_url,
                        allowed_hosts={request.get_host()},
                        require_https=request.is_secure(),
                    ):
                        return redirect(next_url)

                return redirect("employeeHomepage")

            if getattr(form, "pending_message", None):
                messages.warning(request, form.pending_message)
            else:
                messages.error(request, "Invalid email or password.")
        else:
            messages.error(request, "Invalid email or password.")
    else:
        form = EmployeeLoginForm(request=request)

    return render(request, "employeesLogin.html", {"form": form})


# -------------------------------------------------------------------
# Employee Logout
# -------------------------------------------------------------------
def employee_logout(request):
    logout(request)
    return redirect("employeesLogin")


# -------------------------------------------------------------------
# Employee Homepage (Post-login Router)
# -------------------------------------------------------------------
@never_cache
@require_employee_login
def employeeHomepage(request):
    context = request.employee_context

    if not context.is_active_employee:
        raise PermissionDenied("Inactive employee account.")

    role_code = context.role_code  # from AuthorityAssignment via EmployeeContext

    # Branch Manager
    if role_code == "BRANCH_MANAGER":
        branch_id = context.branch_id
        if not branch_id:
            raise PermissionDenied("No branch assigned for manager access.")
        return redirect("branches:manager-dashboard", branch_pk=branch_id)

    # HR roles
    if role_code in {"HR_ADMIN", "BELT_HR_OVERSEER", "SUPER_ADMIN"}:
        return redirect("human_resources:dashboard")

    # Attendant
    if role_code == "ATTENDANT":
        return redirect("jobs:attendant-dashboard")

    # Superuser
    if request.user.is_superuser:
        return redirect("admin:index")

    raise PermissionDenied("No dashboard available for this role.")