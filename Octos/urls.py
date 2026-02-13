from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    path('employees/', include('employees.urls')),
    path('__reload__/', include('django_browser_reload.urls')),

    # Human Resources HTML Routes
    path(
        'hr/',
        include(('Human_Resources.urls', 'human_resources'), namespace='human_resources')
    ),

    # Human Resources API
    path(
        'hr/api/',
        include(('Human_Resources.api.urls', 'hr_api'), namespace='hr_api')
    ),

    path('', include('public.urls')),
    path("api/public/", include("public.api.urls")),

    path("api/", include("branches.urls")),
    path("api/jobs/", include("jobs.urls")),
    path("api/jobs/", include(("jobs.api.urls", "jobs_api"), namespace="jobs_api")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
