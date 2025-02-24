from django.urls import path
from . import views

urlpatterns = [
    path('human_resources/', views.Human_Resources, name='human_resources'),
]