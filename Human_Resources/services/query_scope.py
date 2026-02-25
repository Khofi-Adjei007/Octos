# Human_Resources/services/query_scope.py

from employees.models import Employee
from hr_workflows.models import RecruitmentApplication


def scoped_employee_queryset(user):

    # -------------------------
    # SUPERUSER
    # -------------------------
    if user.is_superuser:
        return Employee.objects.all()

    roles = user.authority_roles.all()

    if not roles.exists():
        return Employee.objects.none()

    # -------------------------
    # SUPER ADMIN
    # -------------------------
    if roles.filter(code="SUPER_ADMIN").exists():
        return Employee.objects.all()

    # -------------------------
    # HR ADMIN (Region Scoped)
    # -------------------------
    if roles.filter(code="HR_ADMIN").exists():

        # If assigned to specific branch → use branch region
        if user.branch and user.branch.region:
            return Employee.objects.filter(
                branch__region=user.branch.region
            )

        # If region stored directly on user (Regional HR)
        if user.region:
            return Employee.objects.filter(
                branch__region__name=user.region
            )

    # -------------------------
    # BELT OVERSEER
    # -------------------------
    if roles.filter(code="BELT_HR_OVERSEER").exists():

        if user.branch and user.branch.region and user.branch.region.belt:
            return Employee.objects.filter(
                branch__region__belt=user.branch.region.belt
            )

    # -------------------------
    # BRANCH MANAGER
    # -------------------------
    if roles.filter(code="BRANCH_MANAGER").exists():

        if user.branch:
            return Employee.objects.filter(
                branch=user.branch
            )

    return Employee.objects.none()


def scoped_recruitment_queryset(user):

    # -------------------------
    # SUPERUSER
    # -------------------------
    if user.is_superuser:
        return RecruitmentApplication.objects.exclude(status="onboarding_complete")

    roles = user.authority_roles.all()

    if not roles.exists():
        return RecruitmentApplication.objects.none()

    # -------------------------
    # SUPER ADMIN
    # -------------------------
    if roles.filter(code="SUPER_ADMIN").exists():
        return RecruitmentApplication.objects.exclude(status="onboarding_complete")

    # -------------------------
    # HR ADMIN (Region Scoped)
    # -------------------------
    if roles.filter(code="HR_ADMIN").exists():

        # Branch-based HR
        if user.branch and user.branch.region:
            return RecruitmentApplication.objects.filter(
                recommended_branch__region=user.branch.region
            ).exclude(status="onboarding_complete")

        # Region-based HR (no branch)
        if user.region:
            return RecruitmentApplication.objects.filter(
                recommended_branch__region__name=user.region
            ).exclude(status="onboarding_complete")

    # -------------------------
    # BELT OVERSEER
    # -------------------------
    if roles.filter(code="BELT_HR_OVERSEER").exists():

        if user.branch and user.branch.region and user.branch.region.belt:
            return RecruitmentApplication.objects.filter(
                recommended_branch__region__belt=user.branch.region.belt
            ).exclude(status="onboarding_complete")

    # -------------------------
    # BRANCH MANAGER
    # -------------------------
    if roles.filter(code="BRANCH_MANAGER").exists():

        if user.branch:
            return RecruitmentApplication.objects.filter(
                recommended_branch=user.branch
            ).exclude(status="onboarding_complete")

    return RecruitmentApplication.objects.none()