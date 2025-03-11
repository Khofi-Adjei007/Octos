from django.shortcuts import render
from django.http import HttpRequest
from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from django.db import IntegrityError
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .employeeForms import EmployeeLoginForm, EmployeeRegistrationForm
# Create your views here.





@never_cache  # Prevents browser caching of the form page
def employeeregistration(request):
    if request.method == 'POST':
        form = EmployeeRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('employeesLogin')
    else:
        form = EmployeeRegistrationForm()  # Blank form on GET
    return render(request, 'employeeregistration.html', {'form': form})



# Login View
@never_cache
def employeesLogin(request):
    if request.method == "POST":
        form = EmployeeLoginForm(request.POST, request=request)  # Pass request
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
                    return redirect("employee_homepage")
    else:
        form = EmployeeLoginForm()  # No request needed for GET
    return render(request, "employeesLogin.html", {"form": form})



# log out view
def employee_logout(request):
    logout(request)
    return redirect('login')  # Redirect to login page after logout


def employeeHomepage(request):
    return redirect('employeeHomepage')