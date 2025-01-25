# employeeForms.py
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from .models import Employee
from django.contrib.auth import login, logout
from django.shortcuts import redirect, render

# Login Form
class EmployeeLoginForm(forms.Form):
    username = forms.CharField(
        label="Username or Email",
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
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("employee_email")
        password = cleaned_data.get("password")

        # Try to authenticate the user
        if email and password:
            user = authenticate(username=email, password=password)
            if user is None:
                raise forms.ValidationError("Invalid email or password.")
        
        return cleaned_data


# Registration Form
class EmployeeRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label='Password')
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')

    class Meta:
        model = Employee
        fields = [
            'first_name', 'middle_name', 'last_name', 'employee_email', 'phone_number',
            'date_of_birth', 'address', 'employee_id', 'position', 'department', 'hire_date', 'salary'
        ]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data

    def save(self, commit=True):
        # Save the employee object first
        employee = super().save(commit=False)

        # Hash the password (you can add more specific logic here)
        employee.set_password(self.cleaned_data['password'])

        if commit:
            employee.save()

        return employee


# Logout Function (No form needed here, we can handle this directly in views)
def employee_logout(request):
    logout(request)
    return redirect('login')  # Redirect to login page after logout
