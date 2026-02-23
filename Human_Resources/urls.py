# Human_Resources/urls.py
from django.urls import path
from . import views
from Human_Resources.api.views.interviewers import InterviewerListAPI

app_name = "human_resources"

urlpatterns = [
    # Dashboard
    path("", views.human_resource, name="dashboard"),

    # Applications tab view (still dashboard-based)
    path("applications/", views.human_resource, name="applications"),

    # Dedicated Application Detail Page
    path(
        "applications/<int:pk>/",
        views.RecruitmentApplicationDetailView.as_view(),
        name="recruitment_application_detail",
    ),

    # Onboarding Detail Page
    path(
        "onboarding/<int:pk>/",
        views.OnboardingDetailView.as_view(),
        name="onboarding_detail",
    ),

    path("employees/", views.human_resource, name="employees"),
    path("departments/", views.human_resource, name="departments"),

    path("approve/<int:employee_id>/", views.approve_employee, name="approve_employee"),
    path("generate-id/<int:employee_id>/", views.generate_employee_id, name="generate_employee_id"),
    path("recommend-employee/", views.recommend_employee, name="recommend_employee"),
    path("branch-manager/", views.branch_manager_dashboard, name="branch_manager_dashboard"),
    path("complete-registration/<str:token>/", views.complete_registration, name="complete_registration"),
    path("interviewers/", InterviewerListAPI.as_view(), name="interviewers"),
]