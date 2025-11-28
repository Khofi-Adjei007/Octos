# employeeForms.py
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect
from .models import Employee, EmergencyContact
from Human_Resources.models import Role

# Login Form
class EmployeeLoginForm(forms.Form):
    username = forms.CharField(
        label="Email",
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-sky-500 focus:border-sky-500 sm:text-sm",
                "id": "username",
            }
        ),
    )

    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-sky-500 focus:border-sky-500 sm:text-sm",
                "id": "password",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.pending_message = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")
        if username and password:
            # Employee.USERNAME_FIELD is employee_email, so authenticate with username parameter works
            user = authenticate(request=self.request if self.request else None, username=username, password=password)
            if user is None:
                # check if a user exists but is inactive (pending approval)
                try:
                    e = Employee.objects.get(employee_email=username)
                    if not e.is_active:
                        self.pending_message = "Your account is pending HR approval."
                        # do not raise validation error yet; allow view to show pending_message
                        return cleaned_data
                except Employee.DoesNotExist:
                    pass
                raise forms.ValidationError("Invalid email or password.")
        return cleaned_data


class EmployeeRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-600 focus:outline-none'}),
        label='Password'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-600 focus:outline-none'}),
        label='Confirm Password'
    )

    # Emergency contact fields (not on Employee model — will be saved to EmergencyContact)
    emergency_contact_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg'}),
        label='Emergency contact name'
    )
    emergency_contact_phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg'}),
        label='Emergency contact phone'
    )

    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg'}),
        label='Requested role'
    )

    class Meta:
        model = Employee
        fields = [
            'first_name', 'middle_name', 'last_name', 'date_of_birth', 'phone_number', 'employee_email',
            'address', 'profile_picture', 'education_level', 'position_title',
            # note: certifications moved to separate model; emergency contact handled below
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg'}),
            'middle_name': forms.TextInput(attrs={'class': 'block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg'}),
            'last_name': forms.TextInput(attrs={'class': 'block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg'}),
            'employee_email': forms.EmailInput(attrs={'class': 'block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg'}),
            'phone_number': forms.TextInput(attrs={'class': 'block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg', 'rows': 3}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg', 'accept': 'image/*'}),
            'education_level': forms.Select(attrs={'class': 'block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg'}),
            'position_title': forms.TextInput(attrs={'class': 'block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        # Save Employee first (ModelForm)
        employee = super().save(commit=False)
        employee.is_active = False  # pending HR approval by default
        # set role if provided
        role_obj = self.cleaned_data.get('role')
        if role_obj:
            employee.role = role_obj
            # optionally set primary_role code
            employee.primary_role = role_obj.name if hasattr(role_obj, 'name') else str(role_obj.pk)
        # set password
        employee.set_password(self.cleaned_data['password'])
        if commit:
            employee.save()

            # create emergency contact if provided
            ec_name = self.cleaned_data.get('emergency_contact_name')
            ec_phone = self.cleaned_data.get('emergency_contact_phone')
            if ec_name or ec_phone:
                EmergencyContact.objects.create(
                    employee=employee,
                    name=ec_name or '',
                    phone=ec_phone or ''
                )
        return employee


# Logout Function
def employee_logout(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('login')
