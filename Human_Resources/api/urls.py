from django.urls import path
from Human_Resources.api.views.overview import HROverviewAPI
from Human_Resources.api.views.recruitment_list import RecruitmentListAPI

app_name = "hr_api"

urlpatterns = [
    path("overview/", HROverviewAPI.as_view(), name="overview"),
    path("applications/", RecruitmentListAPI.as_view(), name="applications"),
]
