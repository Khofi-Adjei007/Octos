"""
URL configuration for Octos project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from Human_Resources import views as hr_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('employees/', include('employees.urls')),
    path('__reload__/', include('django_browser_reload.urls')),
    path('hr/', hr_views.human_resource, name='human_resources'),
    path('', include('public.urls')),
    path("api/public/", include("public.api.urls")),

    # Human Resources API
    path('hr/api/', include('Human_Resources.api.urls', namespace='hr_api')),

    # Branches API
    path("api/", include("branches.urls")),
    path("api/jobs/", include("jobs.urls")),

]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
