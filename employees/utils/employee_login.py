# employees/utils/employee_login.py
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

RedirectDecision = Dict[str, Any]
# Examples:
# {"type": "named", "name": "branches:manager-dashboard", "kwargs": {"branch_pk": 2}}
# {"type": "url", "url": "/some/url/"}

class EmployeeLogin:
    def __init__(self, request, user):
        self.request = request
        self.user = user
        self._profile = None
        self._role_obj = None
        self._role_code = None

    # Public API
    def resolve_redirect(self, next_url: Optional[str] = None) -> Optional[RedirectDecision]:
        """
        Return a RedirectDecision or None. The view should still validate `next_url`
        and handle it before calling this helper (preferred).
        """
        try:
            # Handler order / precedence
            handlers = [
                self._handle_superuser,
                self._handle_branch_manager,
                self._handle_hr_regional,
                self._handle_attendant,
                self._handle_cashier,
                self._handle_default,
            ]
            for h in handlers:
                try:
                    decision = h()
                    if decision:
                        logger.debug("EmployeeLogin resolved via handler %s -> %s", h.__name__, decision)
                        return decision
                except Exception as exc:
                    logger.debug("EmployeeLogin handler %s raised: %s", h.__name__, exc)
            return None
        except Exception as exc:
            logger.exception("EmployeeLogin.resolve_redirect unexpected error: %s", exc)
            return None

    # ----------------
    # Handlers
    # ----------------
    def _handle_superuser(self) -> Optional[RedirectDecision]:
        if getattr(self.user, "is_superuser", False):
            return {"type": "named", "name": "admin:index", "kwargs": {}}
        return None

    def _handle_branch_manager(self) -> Optional[RedirectDecision]:
        """
        Prefer direct managed_branch. Then validate employee.branch -> manager mapping.
        Then fallback to group-based list view.
        """
        profile = self._get_profile()
        try:
            branch = None
            if profile is not None:
                branch = getattr(profile, "managed_branch", None)

            # fallback: if employee.branch exists and branch.manager points to this employee
            if branch is None and profile is not None and getattr(profile, "branch", None):
                candidate = profile.branch
                try:
                    if getattr(candidate, "manager_id", None) == getattr(profile, "pk", None):
                        branch = candidate
                except Exception:
                    branch = None

            if branch is not None:
                return {"type": "named", "name": "branches:manager-dashboard", "kwargs": {"branch_pk": branch.pk}}

            # group fallback: send to branches:list (manager landing)
            if self.user.groups.filter(name="Branch Managers").exists():
                # safe named route; view should provide branches:list
                return {"type": "named", "name": "branches:list", "kwargs": {}}
        except Exception as exc:
            logger.debug("Error in branch manager handler: %s", exc)
        return None

    def _handle_hr_regional(self) -> Optional[RedirectDecision]:
        profile = self._get_profile()
        try:
            if getattr(self.user, "is_staff", False) and profile and getattr(profile, "role", None):
                role_name = getattr(profile.role, "name", "").lower()
                if role_name == "regional_hr_manager" or role_name == "regional hr manager":
                    return {"type": "named", "name": "human_resources", "kwargs": {}}
        except Exception as exc:
            logger.debug("Error in hr regional handler: %s", exc)
        return None

    def _handle_attendant(self) -> Optional[RedirectDecision]:
        if self._get_role_code() == "ATTENDANT":
            return {"type": "named", "name": "attendant_dashboard", "kwargs": {}}
        return None

    def _handle_cashier(self) -> Optional[RedirectDecision]:
        if self._get_role_code() == "CASHIER":
            return {"type": "named", "name": "cashier_dashboard", "kwargs": {}}
        return None

    def _handle_default(self) -> Optional[RedirectDecision]:
        # final fallback
        return {"type": "named", "name": "employeeHomepage", "kwargs": {}}

    # ----------------
    # Helpers
    # ----------------
    def _get_profile(self):
        if self._profile is not None:
            return self._profile

        try:
            # If user is already Employee instance
            from employees.models import Employee
            if isinstance(self.user, Employee):
                self._profile = self.user
                return self._profile
        except Exception:
            pass

        # try common reverse attributes
        for attr in ("userprofile", "employee", "profile"):
            try:
                val = getattr(self.user, attr, None)
                if val is not None:
                    self._profile = val
                    return self._profile
            except Exception:
                continue

        # fallback to query by PK (safe for custom user models)
        try:
            from employees.models import Employee
            pk = getattr(self.user, "pk", None)
            if pk is not None:
                self._profile = Employee.objects.filter(pk=pk).first()
                return self._profile
        except Exception:
            pass

        # last resort: try lookup by email
        try:
            from employees.models import Employee
            email = getattr(self.user, "email", None) or getattr(self.user, "employee_email", None)
            if email:
                self._profile = Employee.objects.filter(employee_email=email).first()
                return self._profile
        except Exception:
            pass

        return None

    def _get_role_obj(self):
        if self._role_obj is not None:
            return self._role_obj

        profile = self._get_profile()
        try:
            if profile and hasattr(profile, "role"):
                self._role_obj = profile.role
                return self._role_obj
        except Exception:
            pass

        try:
            if hasattr(self.user, "role"):
                self._role_obj = getattr(self.user, "role")
                return self._role_obj
        except Exception:
            pass

        return None

    def _get_role_code(self) -> str:
        if self._role_code is not None:
            return self._role_code

        role = self._get_role_obj()
        code = ""
        try:
            if role and getattr(role, "code", None):
                code = getattr(role, "code")
            elif role and getattr(role, "name", None):
                code = getattr(role, "name")
        except Exception:
            code = ""
        self._role_code = (code or "").upper()
        return self._role_code
