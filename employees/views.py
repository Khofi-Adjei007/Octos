"""
employees/views.py

Employee authentication and entry-point views.

Responsibilities:
- Employee registration
- Employee login & logout
- Post-login routing
- Basic employee homepage

Notes:
- Authentication is handled via Django auth
- Authorization decisions are delegated to EmployeeLogin helper
- This file does NOT decide business permissions (manager vs attendant)
"""

import logging

from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.db import IntegrityError

from .models import Employee
from .employeeForms import EmployeeLoginForm, EmployeeRegistrationForm
from .utils.employee_login import EmployeeLogin
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied

from employees.auth.guards import require_employee_login
from employees.auth.permissions import employee_has_permission

from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied

from employees.auth.context import EmployeeContext
from employees.auth.permissions import employee_has_permission

from jobs.services import branch_service

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# Employee Registration
# -------------------------------------------------------------------
@never_cache
def employeeregistration(request):
    """
    Register a new employee account.

    This creates an Employee record and associated auth credentials.
    Approval / activation is handled elsewhere.
    """
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

    return render(
        request,
        "employeeregistration.html",
        {"form": form},
    )


# -------------------------------------------------------------------
# Employee Login
# -------------------------------------------------------------------
@never_cache
def employeesLogin(request):
    """
    Authenticate employee and establish session.

    Responsibilities:
    - Authentication
    - Session creation
    - Safe redirection only

    DOES NOT:
    - Decide dashboard
    - Inspect roles
    - Enforce permissions
    """
    if request.method == "POST":
        form = EmployeeLoginForm(request.POST, request=request)

        if form.is_valid():
            identifier = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            user = authenticate(request, username=identifier, password=password)

            if user is not None:
                login(request, user)
                logger.info("User %s logged in successfully", identifier)

                # --------------------------------------------------
                # 1. Safe ?next= handling
                # --------------------------------------------------
                next_url = request.POST.get("next") or request.GET.get("next")
                if next_url and url_has_allowed_host_and_scheme(
                    next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    return redirect(next_url)

                # --------------------------------------------------
                # 2. Neutral system entry point
                # --------------------------------------------------
                return redirect("employeeHomepage")

            messages.error(request, "Invalid credentials")
            logger.warning("Failed login attempt for %s", identifier)

    else:
        form = EmployeeLoginForm()

    return render(request, "employeesLogin.html", {"form": form})



# -------------------------------------------------------------------
# Employee Logout
# -------------------------------------------------------------------
def employee_logout(request):
    """
    Log out the current employee.
    """
    logout(request)
    return redirect("employeesLogin")


## -------------------------------------------------------------------
# Employee Homepage (Post-login Router)
# -------------------------------------------------------------------
@never_cache
@require_employee_login
def employeeHomepage(request):
    """
    Canonical post-login router.

    Resolves the correct dashboard based on:
    1. Employee activity
    2. Permission priority
    3. Branch scope

    Dashboards themselves only ENFORCE access.
    Routing happens here, once.
    """

    user = request.user
    context = request.employee_context  # already attached by guard

    # --------------------------------------------------
    # 1. Active employee guard
    # --------------------------------------------------
    if not context.is_active_employee:
        raise PermissionDenied("Inactive employee account.")

    # --------------------------------------------------
    # 2. Manager-level permission check (highest priority)
    # --------------------------------------------------
    manager_permissions = (
        "manage_branch",
        "close_day",
        "view_branch_reports",
    )

    if any(employee_has_permission(user, p) for p in manager_permissions):
        branches = branch_service.get_user_branches(user) or []

        if not branches:
            raise PermissionDenied("No branch assigned for manager access.")

        # Single branch → go straight in
        if len(branches) == 1:
            return redirect(
                "branches:manager-dashboard",
                branch_pk=branches[0]["id"],
            )

        # Multiple branches → selector (future-safe)
        return redirect("branches:list")

    # --------------------------------------------------
    # 3. Attendant permission check
    # --------------------------------------------------
    if employee_has_permission(user, "record_job"):
        return redirect("jobs:attendant-dashboard")

    # --------------------------------------------------
    # 4. Absolute fallback
    # --------------------------------------------------
    return redirect("employeesLogin")
