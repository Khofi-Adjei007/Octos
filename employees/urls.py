from django.urls import path
from . import views
from .api.employees_id import employee_id_card_api

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
    path("password-change/", views.force_password_change, name="force_password_change"),
    # --------------------------------------------------
    # ID Card API
    # --------------------------------------------------
    path("api/id-card/", employee_id_card_api, name="employee_id_card"),
    path("api/id-card/<int:pk>/", employee_id_card_api, name="employee_id_card_pk"),
]