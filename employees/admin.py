# employees/admin.py
from django.contrib import admin
from django import forms
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import Employee

class EmployeeCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = Employee
        fields = ('employee_email', 'first_name', 'last_name')

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords don't match")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class EmployeeChangeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = '__all__'

def model_has_field(model, name):
    return any(f.name == name for f in model._meta.get_fields())

class EmployeeAdmin(BaseUserAdmin):
    add_form = EmployeeCreationForm
    form = EmployeeChangeForm
    model = Employee

    list_display = ('employee_email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'department')
    search_fields = ('employee_email', 'first_name', 'last_name')
    ordering = ('employee_email',)

    # Display but not editable
    readonly_fields = tuple(name for name in ('created_at', 'approved_at') if model_has_field(Employee, name))

    # Build safe fieldsets by only including fields that exist on the model
    _fieldsets = [
        (_('Login'), {'fields': ('employee_email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'middle_name', 'last_name', 'phone_number', 'profile_picture')}),
        (_('Work'), {'fields': ('position', 'department', 'branch', 'manager')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('approved_at', 'created_at')}),
    ]

    # Filter unknown fields out
    fieldsets = []
    for title, opts in _fieldsets:
        safe_fields = tuple(f for f in opts.get('fields', ()) if model_has_field(Employee, f))
        if safe_fields:
            fieldsets.append((title, {'fields': safe_fields}))

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': tuple(f for f in ('employee_email', 'first_name', 'last_name', 'password1', 'password2', 'is_staff', 'is_active') if model_has_field(Employee, f) or f.startswith('password')),
        }),
    )

admin.site.register(Employee, EmployeeAdmin)
