from django.shortcuts import render
from django.http import HttpRequest
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .employeeForms import EmployeeLoginForm, EmployeeRegistrationForm
# Create your views here.


def employeesLogin(request):
    form = EmployeeLoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            form.add_error(None, "Invalid username or password.")
    return render(request, "employeesLogin.html", {"form": form})




def employee_register(request):
    if request.method == 'POST':
        form = EmployeeRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # Redirect to login after successful registration
    else:
        form = EmployeeRegistrationForm()

    return render(request, 'register.html', {'form': form})

def employee_logout(request):
    logout(request)
    return redirect('login')  # Redirect to login page after logout


def employeeHomepage(request):
    return redirect('employeeHomepage')