from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

from notifications.models import Notification


class NotificationListAPI(APIView):
    """
    GET /notifications/api/
    Returns the latest 20 notifications for the logged-in user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        notifications = (
            Notification.objects
            .filter(recipient=request.user)
            .select_related("actor")
            .order_by("-created_at")[:20]
        )

        data = [
            {
                "id":         n.pk,
                "verb":       n.verb,
                "message":    n.message,
                "link":       n.link,
                "is_read":    n.is_read,
                "created_at": n.created_at.strftime("%d %b %Y, %H:%M"),
                "actor":      str(n.actor) if n.actor else None,
            }
            for n in notifications
        ]

        return Response(data)


class NotificationUnreadCountAPI(APIView):
    """
    GET /notifications/api/unread-count/
    Returns the unread notification count for the bell badge.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).count()

        return Response({"unread": count})


class NotificationMarkReadAPI(APIView):
    """
    POST /notifications/api/<id>/read/
    Marks a single notification as read.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, recipient=request.user)
        except Notification.DoesNotExist:
            return Response(
                {"error": "Notification not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=["is_read", "read_at"])

        return Response({"ok": True})


class NotificationMarkAllReadAPI(APIView):
    """
    POST /notifications/api/mark-all-read/
    Marks all unread notifications as read for the logged-in user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        updated = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).update(is_read=True, read_at=timezone.now())

        return Response({"ok": True, "marked": updated})