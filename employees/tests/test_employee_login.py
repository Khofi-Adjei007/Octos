# employees/tests/test_employee_login.py
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from employees.utils.employee_login import EmployeeLogin
from branches.models import Branch
from employees.models import Employee

User = get_user_model()

class EmployeeLoginTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = Employee.objects.create_user(employee_email="t1@example.com", password="pass", first_name="T", last_name="User")
        # create branch and assign later in specific tests

    def test_superuser_redirects_admin(self):
        self.user.is_superuser = True
        self.user.save()
        req = self.factory.get('/')
        dec = EmployeeLogin(req, self.user).resolve_redirect()
        self.assertEqual(dec.get("name"), "admin:index")

    # add more tests for branch manager, attendant, etc.
