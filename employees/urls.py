from django.urls import path
from . import views

urlpatterns = [
    path('', views.employeesLogin, name='employeesLogin'),
    path('register/', views.employee_register, name='register'),
    path('logout/', views.employee_logout, name='logout'),
    path('employeeHomepage/', views.employeeHomepage, name='mployeeHomepage')
]
