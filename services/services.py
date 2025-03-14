import logging
import datetime
from django.db.models import Q
from employees.models import Employee
from twilio.rest import Client
from django.conf import settings
import phonenumbers

logger = logging.getLogger(__name__)

class EmployeeService:
    """
    A service class to handle employee-related business logic.
    Designed for scalability, security, and maintainability in an enterprise SaaS.
    """

    def __init__(self):
        self.branch_codes = {
            'FPP-Main': 'MA',
            'FPP-120': 'BR1',
            # Add more branches as needed
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
            branch_name = employee.branch_station.name if employee.branch_station else None
            if not branch_name:
                logger.warning(f"No branch assigned to employee {employee.id}, using default")
                branch_name = 'Unknown'

            branch_code = self.branch_codes.get(branch_name, 'BRX')
            year = datetime.datetime.now().year

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