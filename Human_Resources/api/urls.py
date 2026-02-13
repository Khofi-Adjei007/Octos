from django.urls import path
from Human_Resources.api.views.overview import HROverviewAPI
from Human_Resources.api.views.recruitment_list import RecruitmentListAPI
from Human_Resources.api.views.recruitment_detail import RecruitmentDetailAPI
from Human_Resources.api.views.recruitment_stage_update import RecruitmentStageUpdateAPI
from Human_Resources.api.views.recruitment_evaluation import RecruitmentEvaluationAPI


app_name = "hr_api"

urlpatterns = [
    path("overview/", HROverviewAPI.as_view(), name="overview"),

    path("applications/", RecruitmentListAPI.as_view(), name="applications"),

    path(
        "applications/<int:pk>/",
        RecruitmentDetailAPI.as_view(),
        name="recruitment-detail",
    ),

    path(
        "applications/<int:pk>/stage/",
        RecruitmentStageUpdateAPI.as_view(),
        name="recruitment-stage-update",
    ),

    path(
        "applications/<int:pk>/evaluate/",
        RecruitmentEvaluationAPI.as_view(),
        name="recruitment-evaluation",
    ),
]
