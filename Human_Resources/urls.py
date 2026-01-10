# Human_Resources/urls.py
from django.urls import path
from . import views

app_name = "human_resources"

urlpatterns = [
    path("", views.human_resource, name="dashboard"),
    path("applications/", views.human_resource, name="applications"),
    path("employees/", views.human_resource, name="employees"),
    path("departments/", views.human_resource, name="departments"),

    path("approve/<int:employee_id>/", views.approve_employee, name="approve_employee"),
    path("generate-id/<int:employee_id>/", views.generate_employee_id, name="generate_employee_id"),
    path("recommend-employee/", views.recommend_employee, name="recommend_employee"),
    path("branch-manager/", views.branch_manager_dashboard, name="branch_manager_dashboard"),
    path("complete-registration/<str:token>/", views.complete_registration, name="complete_registration"),
]
