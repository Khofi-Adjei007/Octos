# employees/services/email_service.py

import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)


class EmployeeEmailService:
    """
    Handles all transactional emails to employees.
    """

    @staticmethod
    def send_welcome_email(employee, temp_password: str, branch, role) -> bool:
        """
        Sends branded welcome email with login credentials.
        Returns True if sent successfully, False otherwise.
        """
        try:
            login_url = f"{settings.SITE_URL}/employees/login/" if hasattr(settings, 'SITE_URL') else "http://127.0.0.1:8000/employees/login/"

            context = {
                "first_name": employee.first_name,
                "employee_email": employee.employee_email,
                "temp_password": temp_password,
                "branch_name": branch.name if branch else "Not assigned",
                "role_name": role.name if role else "Not assigned",
                "employee_id": employee.employee_id or "Pending",
                "login_url": login_url,
            }

            html_content = render_to_string("emails/welcome_email.html", context)
            text_content = (
                f"Welcome to Farhat Printing Press, {employee.first_name}!\n\n"
                f"Your account is now active.\n\n"
                f"Email: {employee.employee_email}\n"
                f"Temporary Password: {temp_password}\n"
                f"Branch: {context['branch_name']}\n"
                f"Role: {context['role_name']}\n\n"
                f"Login at: {login_url}\n\n"
                f"You will be required to change your password on first login.\n\n"
                f"HR Department\nFarhat Printing Press"
            )

            msg = EmailMultiAlternatives(
                subject="Welcome to Farhat Printing Press — Your Account is Ready",
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[employee.employee_email],
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()

            logger.info(
                "EmployeeEmailService: welcome email sent to %s",
                employee.employee_email,
            )
            return True

        except Exception as exc:
            logger.error(
                "EmployeeEmailService: failed to send welcome email to %s: %s",
                getattr(employee, "employee_email", "unknown"),
                exc,
            )
            return False