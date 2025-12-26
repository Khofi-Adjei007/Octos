# employees/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # --------------------------------------------------
    # Authentication
    # --------------------------------------------------
    path("login/", views.employeesLogin, name="employeesLogin"),
    path("logout/", views.employee_logout, name="employee_logout"),

    # --------------------------------------------------
    # Post-login system entry point
    # --------------------------------------------------
    path("home/", views.employeeHomepage, name="employeeHomepage"),

    # --------------------------------------------------
    # Employee management
    # --------------------------------------------------
    path("register/", views.employeeregistration, name="employeeregistration"),
]
