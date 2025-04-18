# employeeForms.py
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from .models import Employee
from django.contrib.auth import login, logout
from django.shortcuts import redirect, render
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
            user = authenticate(request=self.request if self.request else None, username=username, password=password)
            print(f"Attempting to authenticate: {username}")
            print(f"Authenticate result: {user}")
            if user is None:
                from employees.models import Employee
                print(f"Checking if user exists with is_active=False: {username}")
                if Employee.objects.filter(employee_email=username, is_active=False).exists():
                    self.pending_message = "Your account is pending HR approval."
                else:
                    print(f"User not found or invalid credentials: {username}")
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

    class Meta:
        model = Employee
        fields = [
            'first_name', 'middle_name', 'last_name', 'date_of_birth', 'phone_number', 'employee_email',
            'address', 'profile_picture', 'education_level', 'certifications', 'skills',
            'emergency_contact_name', 'emergency_contact_phone', 'requested_role',  # Removed 'department'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-600 focus:outline-none'}),
            'middle_name': forms.TextInput(attrs={'class': 'block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-600 focus:outline-none'}),
            'last_name': forms.TextInput(attrs={'class': 'block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-600 focus:outline-none'}),
            'employee_email': forms.EmailInput(attrs={'class': 'block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-600 focus:outline-none'}),
            'phone_number': forms.NumberInput(attrs={'class': 'block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-600 focus:outline-none'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-600 focus:outline-none', 'type': 'date'}),
            'address': forms.TextInput(attrs={
                'class': 'block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-600 focus:outline-none',
                'style': 'height: 3rem;'
            }),
            'profile_picture': forms.ClearableFileInput(attrs={
                'class': 'block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg cursor-pointer focus:ring-2 focus:ring-indigo-600 focus:outline-none',
                'accept': 'image/*',
                'id': 'profile-picture-input',
            }),
            'certifications': forms.TextInput(attrs={'class': 'block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-600 focus:outline-none'}),
            'education_level': forms.Select(attrs={'class': 'block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-600 focus:outline-none'}),
            'skills': forms.TextInput(attrs={'class': 'block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-600 focus:outline-none'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-600 focus:outline-none'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-600 focus:outline-none'}),
            'requested_role': forms.Select(attrs={'class': 'block w-full px-4 py-3 mt-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-600 focus:outline-none'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        employee = super().save(commit=False)
        employee.is_active = False
        employee.set_password(self.cleaned_data['password'])
        if commit:
            employee.save()
        return employee

# Logout Function
def employee_logout(request):
    logout(request)
    return redirect('login')