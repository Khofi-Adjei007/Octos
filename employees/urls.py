from django.urls import path
from . import views

urlpatterns = [
    path('', views.employeesLogin, name='employees_root'),
    path('login/', views.employeesLogin, name='employeesLogin'),
    path('employeeregistration/', views.employeeregistration, name='employeeregistration'),
    path('logout/', views.employee_logout, name='employee_logout'),
    path('homepage/', views.employeeHomepage, name='employeeHomepage'),
]