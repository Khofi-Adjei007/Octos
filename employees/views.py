from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from django.db import IntegrityError
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .employeeForms import EmployeeLoginForm, EmployeeRegistrationForm
from .models import Employee

@never_cache
def employeeregistration(request):
    if request.method == 'POST':
        form = EmployeeRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('employeesLogin')
    else:
        form = EmployeeRegistrationForm()
    return render(request, 'employeeregistration.html', {'form': form})

@never_cache
def employeesLogin(request):
    if request.method == "POST":
        form = EmployeeLoginForm(request.POST, request=request)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if user.is_superuser:
                    return redirect('admin:index')
                elif user.is_staff and user.department == 'HR':
                    return redirect('human_resources')
                else:
                    return redirect("employeeHomepage")
    else:
        form = EmployeeLoginForm()
    return render(request, "employeesLogin.html", {"form": form})

def employee_logout(request):
    logout(request)
    return redirect('employeesLogin')


# Employees Homepage Redirect
@never_cache
@login_required
def employeeHomepage(request):
    try:
        employee = Employee.objects.get(employee_email=request.user.employee_email)
    except Employee.DoesNotExist:
        logout(request)
        return redirect('employeesLogin')
    
    context = {
        'employee': employee,
        'status_message': 'Your application has been approved!' if employee.is_active else 'Your application is pending approval.'
    }
    return render(request, 'employeesHomepage.html', context)