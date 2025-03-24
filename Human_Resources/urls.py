# Human_Resources/urls.py (updated)
from django.urls import path
from . import views

urlpatterns = [
    path('', views.human_resource, name='human_resources'),
    path('approve/<int:employee_id>/', views.approve_employee, name='approve_employee'),
    path('generate-id/<int:employee_id>/', views.generate_employee_id, name='generate_employee_id'),
    path('branch_manager_dashboard/', views.branch_manager_dashboard, name='branch_manager_dashboard'),
    path('recommend-employee/', views.recommend_employee, name='recommend_employee'),
    # Remove the following line if no longer needed
    # path('branch_manager/', views.branch_manager_dashboard_new, name='branch_manager_dashboard_new'),
]