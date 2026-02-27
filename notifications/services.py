"""
notifications.services
======================
Drop-in notification utility. Import and call from anywhere.

Usage
-----
    from notifications.services import notify

    notify(
        recipient = user,
        verb      = "stage_changed",
        message   = "Benjamin Adu's application moved to Interview.",
        link      = "/hr/applications/42/",
        actor     = request.user,   # optional
    )

Bulk notify (multiple recipients at once)
-----------------------------------------
    from notifications.services import notify_many

    notify_many(
        recipients = [hr_manager, reviewer],
        verb       = "offer_extended",
        message    = "An offer has been extended to Ama Mensah.",
        link       = "/hr/applications/7/",
        actor      = request.user,
    )
"""

import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


def notify(*, recipient, verb, message, link="", actor=None):
    """
    Create a single notification.

    Parameters
    ----------
    recipient : User instance
    verb      : str  — one of NotificationVerb values or any free string
    message   : str  — human-readable description shown in the dropdown
    link      : str  — optional relative URL (e.g. "/hr/applications/42/")
    actor     : User instance or None — who triggered the notification
    """
    if recipient is None:
        logger.warning("notify() called with recipient=None — skipped.")
        return None

    # Late import to avoid circular imports
    from notifications.models import Notification

    try:
        notification = Notification.objects.create(
            recipient=recipient,
            actor=actor,
            verb=verb,
            message=message,
            link=link,
        )
        logger.debug(
            "Notification created: verb=%s recipient=%s",
            verb,
            recipient,
        )
        return notification
    except Exception as exc:
        # Never let a notification failure crash the main request
        logger.error("Failed to create notification: %s", exc)
        return None


def notify_many(*, recipients, verb, message, link="", actor=None):
    """
    Create the same notification for multiple recipients.
    Skips None entries silently.
    """
    created = []
    for recipient in recipients:
        if recipient is not None:
            n = notify(
                recipient=recipient,
                verb=verb,
                message=message,
                link=link,
                actor=actor,
            )
            if n:
                created.append(n)
    return created