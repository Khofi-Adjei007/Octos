from django.urls import path
from . import views

urlpatterns = [
    path('', views.employeesLogin, name='employeesLogin'),
    path('employeeregistration/', views.employeeregistration, name='employeeregistration'),
    path('logout/', views.employee_logout, name='logout'),
    path('employeeHomepage/', views.employeeHomepage, name='employeeHomepage'),
]