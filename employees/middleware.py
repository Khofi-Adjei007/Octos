# employees/middleware.py

from django.shortcuts import redirect
from django.urls import reverse


EXEMPT_URLS = [
    "/employees/login/",
    "/employees/logout/",
    "/employees/password-change/",
    "/admin/",
    "/static/",
    "/media/",
]


class ForcePasswordChangeMiddleware:
    """
    Redirects authenticated employees to password change page
    if must_change_password is True.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user

        if (
            user.is_authenticated
            and hasattr(user, "must_change_password")
            and user.must_change_password
        ):
            current_path = request.path
            exempt = any(current_path.startswith(url) for url in EXEMPT_URLS)

            if not exempt:
                return redirect(reverse("force_password_change"))

        return self.get_response(request)