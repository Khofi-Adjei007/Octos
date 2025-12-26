from django.urls import path
from jobs.views_receipts import job_receipt_pdf
from .views import attendant_dashboard
from .api.views import job_receipt  


urlpatterns = [
    path("ui/attendant/", attendant_dashboard, name="attendant_dashboard"),
    path("receipt/<int:job_id>/", job_receipt, name="job_receipt"),
    path("receipt/<int:job_id>/pdf/", job_receipt_pdf, name="job_receipt_pdf"),
]
