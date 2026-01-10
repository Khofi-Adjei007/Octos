# employees/employeeForms.py

from django import forms
from django.contrib.auth import authenticate
from django.shortcuts import redirect

from employees.models import Employee, EmergencyContact
from Human_Resources.models import Role


# ============================================================
# Employee Login Form
# ============================================================
class EmployeeLoginForm(forms.Form):
    username = forms.CharField(
        label="Email",
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "class": (
                    "mt-1 block w-full px-3 py-2 border border-gray-300 "
                    "rounded-md shadow-sm focus:outline-none focus:ring-sky-500 "
                    "focus:border-sky-500 sm:text-sm"
                ),
                "id": "username",
            }
        ),
    )

    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": (
                    "mt-1 block w-full px-3 py-2 border border-gray-300 "
                    "rounded-md shadow-sm focus:outline-none focus:ring-sky-500 "
                    "focus:border-sky-500 sm:text-sm"
                ),
                "id": "password",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.pending_message = None
        self.user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if not username or not password:
            return cleaned_data

        # -------------------------------------------------
        # 1. Resolve employee (ignore soft-deleted users)
        # -------------------------------------------------
        try:
            employee = Employee.objects.get(
                employee_email=username,
                deleted_at__isnull=True
            )
        except Employee.DoesNotExist:
            raise forms.ValidationError("Invalid email or password.")

        # -------------------------------------------------
        # 2. HR approval gate
        # -------------------------------------------------
        if employee.approved_at is None:
            self.pending_message = "Your account is pending HR approval."
            return cleaned_data

        # -------------------------------------------------
        # 3. Activation gate (suspension / leave)
        # -------------------------------------------------
        if not employee.is_active:
            self.pending_message = "Your account is temporarily disabled. Contact HR."
            return cleaned_data

        # -------------------------------------------------
        # 4. Branch assignment gate (role-aware)
        # -------------------------------------------------
        BRANCH_EXEMPT_ROLES = {
            "HR_MANAGER",
            "HR_MANAGER_SOUTH",
            "HR_MANAGER_MID",
            "HR_MANAGER_NORTH",
            "super_admin",
            "admin",
        }
        employee_role_code = employee.role.code if employee.role else None

        if employee.branch is None and employee_role_code not in BRANCH_EXEMPT_ROLES:
            self.pending_message = "Your account is not assigned to a branch. Contact HR."
            return cleaned_data


        # -------------------------------------------------
        # 5. Authenticate credentials LAST
        # -------------------------------------------------
        user = authenticate(
            request=self.request if self.request else None,
            username=username,
            password=password,
        )

        if user is None:
            raise forms.ValidationError("Invalid email or password.")

        self.user = user
        return cleaned_data


# ============================================================
# Employee Registration Form (HR approval required)
# ============================================================
class EmployeeRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": (
                    "block w-full px-4 py-3 mt-2 border border-gray-300 "
                    "rounded-lg focus:ring-2 focus:ring-indigo-600 focus:outline-none"
                )
            }
        ),
        label="Password",
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": (
                    "block w-full px-4 py-3 mt-2 border border-gray-300 "
                    "rounded-lg focus:ring-2 focus:ring-indigo-600 focus:outline-none"
                )
            }
        ),
        label="Confirm Password",
    )

    # Emergency contact (stored separately)
    emergency_contact_name = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg"}
        ),
        label="Emergency contact name",
    )

    emergency_contact_phone = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg"}
        ),
        label="Emergency contact phone",
    )

    # Requested role (NOT authoritative)
    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        required=False,
        widget=forms.Select(
            attrs={"class": "block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg"}
        ),
        label="Requested role",
    )

    class Meta:
        model = Employee
        fields = [
            "first_name",
            "middle_name",
            "last_name",
            "date_of_birth",
            "phone_number",
            "employee_email",
            "address",
            "profile_picture",
            "education_level",
            "position_title",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg"}),
            "middle_name": forms.TextInput(attrs={"class": "block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg"}),
            "last_name": forms.TextInput(attrs={"class": "block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg"}),
            "employee_email": forms.EmailInput(attrs={"class": "block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg"}),
            "phone_number": forms.TextInput(attrs={"class": "block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg"}),
            "date_of_birth": forms.DateInput(
                attrs={
                    "class": "block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg",
                    "type": "date",
                }
            ),
            "address": forms.Textarea(
                attrs={
                    "class": "block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg",
                    "rows": 3,
                }
            ),
            "profile_picture": forms.ClearableFileInput(
                attrs={
                    "class": "block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg",
                    "accept": "image/*",
                }
            ),
            "education_level": forms.Select(attrs={"class": "block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg"}),
            "position_title": forms.TextInput(attrs={"class": "block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data

    def save(self, commit=True):
        employee = super().save(commit=False)

        # -------------------------------------------------
        # HR approval defaults (CRITICAL)
        # -------------------------------------------------
        employee.is_active = False
        employee.approved_at = None
        employee.branch = None

        # -------------------------------------------------
        # Requested role only (NOT authoritative)
        # -------------------------------------------------
        role_obj = self.cleaned_data.get("role")
        if role_obj:
            employee.primary_role = (
                role_obj.name if hasattr(role_obj, "name") else str(role_obj.pk)
            )

        # -------------------------------------------------
        # Password
        # -------------------------------------------------
        employee.set_password(self.cleaned_data["password"])

        if commit:
            employee.save()

            # Emergency contact (optional)
            ec_name = self.cleaned_data.get("emergency_contact_name")
            ec_phone = self.cleaned_data.get("emergency_contact_phone")
            if ec_name or ec_phone:
                EmergencyContact.objects.create(
                    employee=employee,
                    name=ec_name or "",
                    phone=ec_phone or "",
                )

        return employee


# ============================================================
# Logout
# ============================================================
def employee_logout(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect("employeesLogin")
