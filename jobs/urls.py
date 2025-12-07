from django.urls import path
from .views import attendant_dashboard
from .api.views import job_receipt   # still allowed for backward compatibility

urlpatterns = [
    path("ui/attendant/", attendant_dashboard, name="attendant_dashboard"),
    path("receipt/<int:job_id>/", job_receipt, name="job_receipt"),
]
