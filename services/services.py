# services/services.py
import logging
import datetime
from django.db import models
from django.db.models import Avg, Count
from employees.models import Employee
from branches.models import Branch  # Updated import
from twilio.rest import Client
from django.conf import settings
import phonenumbers
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)

class EmployeeService:
    """
    A service class to handle employee-related business logic.
    Designed for scalability, security, and maintainability in an enterprise SaaS.
    """

    def __init__(self):
            self.branch_codes = {
                'FPP-Main': 'MA',
                'FPP-North': 'NTH',
                'FPP-South': 'STH',
                'FPP-East': 'EST',
                'FPP-West': 'WST',
            }

    def generate_employee_id(self, employee):
        """
        Generate a unique employee ID in the format FPP-YYYY-BranchCode-NNN.
        Ensures no duplicates by checking the database.
        """
        if not isinstance(employee, Employee):
            logger.error("Invalid employee object provided for ID generation")
            raise ValueError("Invalid employee object")

        try:
            branch_name = employee.branch.name if employee.branch else None  # Updated to use branch
            if not branch_name:
                logger.warning(f"No branch assigned to employee {employee.id}, using default")
                branch_name = 'Unknown'

            branch_code = self.branch_codes.get(branch_name, 'BRX')
            year = datetime.now().year

            last_employee = Employee.objects.filter(
                employee_id__startswith=f"FPP-{year}-{branch_code}-"
            ).order_by('-employee_id').first()

            last_number = 'A1A'
            if last_employee and last_employee.employee_id:
                last_number = last_employee.employee_id.split('-')[-1]

            new_number = self._increment_alphanumeric(last_number)
            new_employee_id = f"FPP-{year}-{branch_code}-{new_number}"

            while Employee.objects.filter(employee_id=new_employee_id).exists():
                logger.warning(f"ID {new_employee_id} already exists, incrementing again")
                new_number = self._increment_alphanumeric(new_number)
                new_employee_id = f"FPP-{year}-{branch_code}-{new_number}"

            logger.info(f"Generated employee ID for {employee.id}: {new_employee_id}")
            return new_employee_id
        except Exception as e:
            logger.error(f"Error generating employee ID for {employee.id}: {str(e)}")
            raise

    def send_approval_sms(self, employee):
        """
        Send an approval SMS to the employee using Twilio.

        Args:
            employee: Employee instance

        Returns:
            bool: True if SMS was sent successfully, False otherwise
        """
        if not isinstance(employee, Employee):
            logger.error("Invalid employee object provided for SMS")
            raise ValueError("Invalid employee object")

        # Validate phone number with default region "GH" (Ghana)
        to_number = employee.phone_number
        try:
            # If the number doesn't start with "+", assume it's a local Ghanaian number
            if not to_number.startswith('+'):
                parsed_number = phonenumbers.parse(to_number, "GH")
            else:
                parsed_number = phonenumbers.parse(to_number)
            
            if not phonenumbers.is_valid_number(parsed_number):
                logger.error(f"Invalid phone number for employee {employee.id}: {to_number}")
                return False
            to_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException as e:
            logger.error(f"Failed to parse phone number for employee {employee.id}: {to_number}, error: {str(e)}")
            return False

        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            message = client.messages.create(
                body=f"Dear {employee.first_name} {employee.last_name}, congratulations! Your application with Farhart Printing Press has been approved. Please check back to sign in.",
                from_=settings.TWILIO_PHONE_NUMBER,
                to=to_number
            )
            logger.info(f"SMS sent to {to_number} for employee {employee.id}: {message.sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS to {to_number} for employee {employee.id}: {str(e)}")
            return False

    def _increment_alphanumeric(self, current):
        """Increment an alphanumeric sequence (e.g., A1A -> A1B)."""
        chars = list(current)
        carry = True
        for i in range(len(chars) - 1, -1, -1):
            if not carry:
                break
            if chars[i] == 'Z':
                chars[i] = 'A'
            elif chars[i] == '9':
                chars[i] = '0'
            else:
                chars[i] = chr(ord(chars[i]) + 1)
                carry = False
            if i == 0 and carry:
                chars.insert(0, 'A')
        return ''.join(chars)


class MetricsService:
    """
    A service class to handle metrics-related calculations across the system.
    Designed for reusability and scalability in an enterprise SaaS.
    """

    def calculate_recruitment_metrics(self, date_filter, today):
        """
        Calculate recruitment metrics, trends, and date range based on the given date filter.
        Args:
            date_filter (str): 'this_month', 'last_month', or 'this_year'
            today (datetime.date): The current date for calculations
        Returns:
            dict: Metrics, trends, and date range
        """
        try:
            # Handle Date Range
            if date_filter == 'this_month':
                start_date = today.replace(day=1)
                end_date = today
            elif date_filter == 'last_month':
                end_date = today.replace(day=1) - timedelta(days=1)
                start_date = end_date.replace(day=1)
            elif date_filter == 'this_year':
                start_date = today.replace(month=1, day=1)
                end_date = today
            else:  # Default to this year
                start_date = today.replace(month=1, day=1)
                end_date = today

            # Format the date range for display
            date_range = f"From {start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"

            # Previous period for trend calculation
            if date_filter == 'this_month':
                prev_end_date = start_date - timedelta(days=1)
                prev_start_date = prev_end_date.replace(day=1)
            elif date_filter == 'last_month':
                prev_end_date = start_date - timedelta(days=1)
                prev_start_date = prev_end_date.replace(day=1)
            else:  # This year
                prev_end_date = start_date - timedelta(days=1)
                prev_start_date = prev_end_date.replace(month=1, day=1)

            # Calculate Metrics
            # 1. Total Pending Approvals
            total_pending = Employee.objects.filter(
                is_active=False,  # Updated to use is_active
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            ).count()
            total_pending_prev = Employee.objects.filter(
                is_active=False,
                created_at__date__gte=prev_start_date,
                created_at__date__lte=prev_end_date
            ).count()
            total_pending_trend = self._calculate_trend(total_pending, total_pending_prev)

            # 2. Avg. Time to Approve
            approved_employees = Employee.objects.filter(
                is_active=True,  # Updated to use is_active
                approved_at__gte=start_date,  # Updated to use approved_at
                approved_at__lte=end_date,
                created_at__isnull=False,
                approved_at__isnull=False
            )
            avg_days_to_approve = 0
            if approved_employees.exists():
                avg_days = approved_employees.aggregate(
                    avg_time=Avg('approved_at', output_field=models.DurationField()) - Avg('created_at', output_field=models.DurationField())
                )['avg_time']
                avg_days_to_approve = round(avg_days.total_seconds() / (60 * 60 * 24), 1) if avg_days else 0
            # Previous period for trend
            approved_employees_prev = Employee.objects.filter(
                is_active=True,
                approved_at__gte=prev_start_date,
                approved_at__lte=prev_end_date,
                created_at__isnull=False,
                approved_at__isnull=False
            )
            avg_days_to_approve_prev = 0
            if approved_employees_prev.exists():
                avg_days_prev = approved_employees_prev.aggregate(
                    avg_time=Avg('approved_at', output_field=models.DurationField()) - Avg('created_at', output_field=models.DurationField())
                )['avg_time']
                avg_days_to_approve_prev = round(avg_days_prev.total_seconds() / (60 * 60 * 24), 1) if avg_days_prev else 0
            avg_days_to_approve_trend = self._calculate_trend(avg_days_to_approve, avg_days_to_approve_prev)

            # 3. Applicants In Last Month (Last 30 days)
            last_30_days_start = today - timedelta(days=30)
            total_employees = Employee.objects.filter(
                created_at__date__gte=last_30_days_start,
                created_at__date__lte=end_date
            ).count()
            prev_30_days_start = last_30_days_start - timedelta(days=30)
            prev_30_days_end = last_30_days_start - timedelta(days=1)
            total_employees_prev = Employee.objects.filter(
                created_at__date__gte=prev_30_days_start,
                created_at__date__lte=prev_30_days_end
            ).count()
            total_employees_trend = self._calculate_trend(total_employees, total_employees_prev)

            # 4. Approved Applicants
            active_employees = Employee.objects.filter(
                is_active=True,  # Updated to use is_active
                approved_at__gte=start_date,
                approved_at__lte=end_date
            ).count()
            active_employees_prev = Employee.objects.filter(
                is_active=True,
                approved_at__gte=prev_start_date,
                approved_at__lte=prev_end_date
            ).count()
            active_employees_trend = self._calculate_trend(active_employees, active_employees_prev)

            # 5. Total Branches
            total_branches = Branch.objects.count()  # Updated to use Branch
            total_branches_prev = total_branches  # Assuming branches don't change frequently
            total_branches_trend = self._calculate_trend(total_branches, total_branches_prev)

            logger.info(f"Successfully calculated recruitment metrics for date filter: {date_filter}")
            return {
                'total_pending': total_pending,
                'total_pending_trend': total_pending_trend,
                'avg_days_to_approve': avg_days_to_approve,
                'avg_days_to_approve_trend': avg_days_to_approve_trend,
                'total_employees': total_employees,
                'total_employees_trend': total_employees_trend,
                'active_employees': active_employees,
                'active_employees_trend': active_employees_trend,
                'total_branches': total_branches,
                'total_branches_trend': total_branches_trend,
                'date_range': date_range,
                'date_filter': date_filter,
            }
        except Exception as e:
            logger.error(f"Error calculating recruitment metrics: {str(e)}")
            raise

    def _calculate_trend(self, current, previous):
        """
        Calculate the percentage trend between current and previous values.
        Args:
            current (float): Current value
            previous (float): Previous value
        Returns:
            float: Percentage change
        """
        if previous == 0:
            return 0 if current == 0 else 100 if current > 0 else -100
        return round(((current - previous) / previous) * 100, 1)