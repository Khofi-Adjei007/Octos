# Human_Resources/recruitment_services/exceptions.py

class RecruitmentError(Exception):
    """Base class for all recruitment domain errors."""
    pass


class PermissionDenied(RecruitmentError):
    pass


class InvalidTransition(RecruitmentError):
    pass


class HiringError(RecruitmentError):
    pass
