# employees/auth/exceptions.py

class EmployeeAuthError(Exception):
    """
    Base exception for employee authentication / authorization errors.
    """
    pass


class InactiveEmployeeError(EmployeeAuthError):
    """
    Raised when an employee account exists but is not allowed to act.
    """
    pass


class MissingPermissionError(EmployeeAuthError):
    """
    Raised when an employee lacks a required permission.
    """
    pass
