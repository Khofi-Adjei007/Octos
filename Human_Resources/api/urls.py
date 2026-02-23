from django.urls import path
from Human_Resources.api.views.overview import HROverviewAPI
from Human_Resources.api.views.recruitment_list import RecruitmentListAPI
from Human_Resources.api.views.recruitment_detail import RecruitmentDetailAPI
from Human_Resources.api.views.recruitment_evaluation import RecruitmentEvaluationAPI
from Human_Resources.api.views.branches import BranchListAPI
from .views.recruitment_transition import RecruitmentTransitionAPI
from Human_Resources.api.views.interviewers import InterviewerListAPI
from Human_Resources.api.views.onboarding import (
    OnboardingInitiateAPI,
    OnboardingPhaseOneAPI,
    OnboardingPhaseTwoAPI,
    OnboardingPhaseThreeAPI,
    OnboardingStatusAPI,
)


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
        "applications/<int:pk>/evaluate/",
        RecruitmentEvaluationAPI.as_view(),
        name="recruitment-evaluation",
    ),

    path(
        "recruitment/<int:pk>/transition/",
        RecruitmentTransitionAPI.as_view(),
        name="recruitment-transition",
    ),

    path("branches/", BranchListAPI.as_view(), name="branches"),

    # Add to urlpatterns:
    path("onboarding/<int:pk>/initiate/", OnboardingInitiateAPI.as_view(), name="onboarding-initiate"),
    path("onboarding/<int:pk>/phase-one/", OnboardingPhaseOneAPI.as_view(), name="onboarding-phase-one"),
    path("onboarding/<int:pk>/phase-two/", OnboardingPhaseTwoAPI.as_view(), name="onboarding-phase-two"),
    path("onboarding/<int:pk>/phase-three/", OnboardingPhaseThreeAPI.as_view(), name="onboarding-phase-three"),
    path("onboarding/<int:pk>/status/", OnboardingStatusAPI.as_view(), name="onboarding-status"),
    path("interviewers/", InterviewerListAPI.as_view(), name="interviewers"),
]


