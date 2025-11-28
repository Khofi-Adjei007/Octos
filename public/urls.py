from django.urls import path
from . import views

app_name = 'public'
urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
    path('contact/', views.contact, name='contact'),
    path('careers/', views.careers, name='careers'),
    path('apply/', views.public_apply, name='apply'),
    
    #public application api endpoint
]
