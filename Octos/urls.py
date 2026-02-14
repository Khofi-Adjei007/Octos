from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.urls import re_path
from django.views.decorators.clickjacking import xframe_options_exempt

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
    urlpatterns += [
        re_path(
            r'^media/(?P<path>.*)$',
            xframe_options_exempt(serve),
            {'document_root': settings.MEDIA_ROOT},
        ),
    ]
