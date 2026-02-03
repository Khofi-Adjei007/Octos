from django.urls import path
from Human_Resources.api import views as api_views
from Human_Resources.api.views.recruitment import RecommendCandidateView

app_name = "hr_api"

urlpatterns = [
    # =========================================================
    # 🚫 Legacy Public Applications (temporarily disabled)
    # =========================================================
    # path("applications/", api_views.application_list, name="applications-list"),
    # path("applications/<int:pk>/", api_views.application_detail, name="applications-detail"),
    # path("applications/<int:pk>/approve/", api_views.application_approve, name="applications-approve"),
    # path("applications/<int:pk>/reject/", api_views.application_reject, name="applications-reject"),

    # =========================================================
    # Employees
    # =========================================================
    # path("employees/", api_views.employee_list, name="employees-list"),
    # path("employees/create/", api_views.employee_create, name="employees-create"),
    # path("employees/<int:pk>/", api_views.employee_detail, name="employees-detail"),
    # path("employees/<int:pk>/set-department/", api_views.employee_set_department,name="employees-set-department",),

    # =========================================================
    # Complaints
    # =========================================================
    # path("complaints/", api_views.complaint_list, name="complaints-list"),
    # path("complaints/create/", api_views.complaint_create, name="complaints-create"),
    # path("complaints/<int:pk>/", api_views.complaint_detail, name="complaints-detail"),
    # path("complaints/<int:pk>/resolve/", api_views.complaint_resolve, name="complaints-resolve"),

    # =========================================================
    # Messaging
    # =========================================================
    # path("messages/", api_views.message_list, name="messages-list"),
    # path("messages/create/", api_views.message_create, name="messages-create"),
    # path("messages/<int:pk>/", api_views.message_detail, name="messages-detail"),
    # path("messages/<int:pk>/mark-read/", api_views.message_mark_read, name="messages-mark-read"),

    # =========================================================
    # Departments
    # =========================================================
    # path("departments/", api_views.department_list, name="departments-list"),

    # =========================================================
    # Payroll
    # =========================================================
    # path("payroll/", api_views.payroll_list, name="payroll-list"),
    # path("payroll/create/", api_views.payroll_create, name="payroll-create"),
    # path("payroll/<int:pk>/", api_views.payroll_detail, name="payroll-detail"),

    # =========================================================
    # Performance Reviews
    # =========================================================
    # path("reviews/", api_views.review_list, name="reviews-list"),
    # path("reviews/create/", api_views.review_create, name="reviews-create"),
    # path("reviews/<int:pk>/", api_views.review_detail, name="reviews-detail"),

    # =========================================================
    # Training Sessions
    # =========================================================
    # path("trainings/", api_views.training_list, name="trainings-list"),
    # path("trainings/create/", api_views.training_create, name="trainings-create"),
    # path("trainings/<int:pk>/", api_views.training_detail, name="trainings-detail"),

    # =========================================================
    # Recruitment (NEW FLOW)
    # =========================================================
    # path("recruitment/recommend/", RecommendCandidateView.as_view(), name="recruit-candidate"),
]
