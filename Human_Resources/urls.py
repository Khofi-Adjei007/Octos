# Human_Resources/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.human_resource, name='human_resources'),
    path('approve/<int:employee_id>/', views.approve_employee, name='approve_employee'),
    path('generate-id/<int:employee_id>/', views.generate_employee_id, name='generate_employee_id'),
]