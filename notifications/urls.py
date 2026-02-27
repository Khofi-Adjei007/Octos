from django.urls import path
from notifications.api_views import (
    NotificationListAPI,
    NotificationUnreadCountAPI,
    NotificationMarkReadAPI,
    NotificationMarkAllReadAPI,
)

app_name = "notifications"

urlpatterns = [
    path("",                  NotificationListAPI.as_view(),        name="list"),
    path("unread-count/",     NotificationUnreadCountAPI.as_view(), name="unread-count"),
    path("mark-all-read/",    NotificationMarkAllReadAPI.as_view(), name="mark-all-read"),
    path("<int:pk>/read/",    NotificationMarkReadAPI.as_view(),    name="mark-read"),
]