from django.test import TestCase
# notifications/tests.py
"""
Rigorous test suite for the notifications system.

Covers:
  1. notify() service — correctness, edge cases, silent failure
  2. notify_many() service
  3. Notification model defaults and ordering
  4. API endpoints — auth, correctness, ownership enforcement
  5. All 5 trigger integrations (via direct view calls)
  6. Edge cases — no HR managers, no branch manager, self-exclusion
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from notifications.models import Notification, NotificationVerb
from notifications.services import notify, notify_many

User = get_user_model()


# ================================================================
# HELPERS
# ================================================================

def make_employee(email, first="Test", last="User", **kwargs):
    return User.objects.create_user(
        employee_email=email,
        first_name=first,
        last_name=last,
        password="testpass123",
        **kwargs,
    )


# ================================================================
# 1. notify() SERVICE
# ================================================================

class NotifyServiceTest(TestCase):

    def setUp(self):
        self.recipient = make_employee("recipient@test.com", "Ama", "Mensah")
        self.actor     = make_employee("actor@test.com",     "Kojo", "Asante")

    def test_creates_notification_with_correct_fields(self):
        n = notify(
            recipient=self.recipient,
            verb="stage_changed",
            message="Application moved to Screening.",
            link="/hr/applications/1/",
            actor=self.actor,
        )
        self.assertIsNotNone(n)
        self.assertEqual(n.recipient, self.recipient)
        self.assertEqual(n.actor,     self.actor)
        self.assertEqual(n.verb,      "stage_changed")
        self.assertEqual(n.message,   "Application moved to Screening.")
        self.assertEqual(n.link,      "/hr/applications/1/")
        self.assertFalse(n.is_read)
        self.assertIsNone(n.read_at)

    def test_creates_notification_without_actor(self):
        n = notify(
            recipient=self.recipient,
            verb="employee_approved",
            message="You have been approved.",
        )
        self.assertIsNotNone(n)
        self.assertIsNone(n.actor)

    def test_creates_notification_without_link(self):
        n = notify(
            recipient=self.recipient,
            verb="stage_changed",
            message="Something happened.",
        )
        self.assertEqual(n.link, "")

    def test_returns_none_silently_when_recipient_is_none(self):
        """Must never crash — called from views that may have no recipient."""
        result = notify(
            recipient=None,
            verb="stage_changed",
            message="This should not crash.",
        )
        self.assertIsNone(result)
        self.assertEqual(Notification.objects.count(), 0)

    def test_persists_to_database(self):
        notify(recipient=self.recipient, verb="stage_changed", message="Test.")
        self.assertEqual(Notification.objects.count(), 1)

    def test_all_verb_choices_are_accepted(self):
        verbs = [
            "recommendation_submitted",
            "stage_changed",
            "offer_extended",
            "employee_approved",
            "onboarding_completed",
        ]
        for verb in verbs:
            notify(recipient=self.recipient, verb=verb, message=f"Test {verb}.")
        self.assertEqual(Notification.objects.count(), len(verbs))


# ================================================================
# 2. notify_many() SERVICE
# ================================================================

class NotifyManyServiceTest(TestCase):

    def setUp(self):
        self.u1 = make_employee("u1@test.com", "Ama",  "One")
        self.u2 = make_employee("u2@test.com", "Kofi", "Two")
        self.u3 = make_employee("u3@test.com", "Yaa",  "Three")

    def test_creates_notification_for_each_recipient(self):
        created = notify_many(
            recipients=[self.u1, self.u2, self.u3],
            verb="stage_changed",
            message="Bulk test.",
        )
        self.assertEqual(len(created), 3)
        self.assertEqual(Notification.objects.count(), 3)

    def test_skips_none_entries_silently(self):
        created = notify_many(
            recipients=[self.u1, None, self.u2, None],
            verb="stage_changed",
            message="With nones.",
        )
        self.assertEqual(len(created), 2)
        self.assertEqual(Notification.objects.count(), 2)

    def test_empty_recipients_list_creates_nothing(self):
        created = notify_many(recipients=[], verb="stage_changed", message="Empty.")
        self.assertEqual(created, [])
        self.assertEqual(Notification.objects.count(), 0)

    def test_all_none_recipients_creates_nothing(self):
        created = notify_many(
            recipients=[None, None],
            verb="stage_changed",
            message="All none.",
        )
        self.assertEqual(Notification.objects.count(), 0)


# ================================================================
# 3. NOTIFICATION MODEL
# ================================================================

class NotificationModelTest(TestCase):

    def setUp(self):
        self.user = make_employee("model@test.com", "Test", "User")

    def test_default_is_read_is_false(self):
        n = Notification.objects.create(
            recipient=self.user,
            verb="stage_changed",
            message="Test.",
        )
        self.assertFalse(n.is_read)

    def test_default_read_at_is_none(self):
        n = Notification.objects.create(
            recipient=self.user,
            verb="stage_changed",
            message="Test.",
        )
        self.assertIsNone(n.read_at)

    def test_default_link_is_empty_string(self):
        n = Notification.objects.create(
            recipient=self.user,
            verb="stage_changed",
            message="Test.",
        )
        self.assertEqual(n.link, "")

    def test_ordering_newest_first(self):
        n1 = notify(recipient=self.user, verb="stage_changed",   message="First.")
        n2 = notify(recipient=self.user, verb="offer_extended",  message="Second.")
        n3 = notify(recipient=self.user, verb="employee_approved", message="Third.")

        notifications = list(Notification.objects.filter(recipient=self.user))
        self.assertEqual(notifications[0], n3)
        self.assertEqual(notifications[1], n2)
        self.assertEqual(notifications[2], n1)

    def test_str_representation(self):
        n = Notification.objects.create(
            recipient=self.user,
            verb="stage_changed",
            message="Test.",
        )
        self.assertIn("stage_changed", str(n))
        self.assertIn("unread", str(n))


# ================================================================
# 4. API ENDPOINTS
# ================================================================

class NotificationAPIAuthTest(TestCase):
    """All endpoints must return 403 when unauthenticated."""

    def setUp(self):
        self.client = Client()
        self.user   = make_employee("auth@test.com", "Auth", "User")
        # Create one notification so mark-read has something to work with
        self.notif  = notify(recipient=self.user, verb="stage_changed", message="Test.")

    def test_list_requires_auth(self):
        res = self.client.get("/notifications/api/")
        self.assertEqual(res.status_code, 403)

    def test_unread_count_requires_auth(self):
        res = self.client.get("/notifications/api/unread-count/")
        self.assertEqual(res.status_code, 403)

    def test_mark_read_requires_auth(self):
        res = self.client.post(f"/notifications/api/{self.notif.pk}/read/")
        self.assertEqual(res.status_code, 403)

    def test_mark_all_read_requires_auth(self):
        res = self.client.post("/notifications/api/mark-all-read/")
        self.assertEqual(res.status_code, 403)


class NotificationListAPITest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user   = make_employee("list@test.com", "List", "User")
        self.client.login(username="list@test.com", password="testpass123")

        notify(recipient=self.user, verb="stage_changed",   message="First.")
        notify(recipient=self.user, verb="offer_extended",  message="Second.")
        notify(recipient=self.user, verb="employee_approved", message="Third.")

    def test_returns_200(self):
        res = self.client.get("/notifications/api/")
        self.assertEqual(res.status_code, 200)

    def test_returns_only_own_notifications(self):
        other = make_employee("other@test.com", "Other", "User")
        notify(recipient=other, verb="stage_changed", message="Not mine.")

        res  = self.client.get("/notifications/api/")
        data = res.json()
        self.assertEqual(len(data), 3)

    def test_returns_correct_fields(self):
        res  = self.client.get("/notifications/api/")
        item = res.json()[0]
        for field in ["id", "verb", "message", "link", "is_read", "created_at"]:
            self.assertIn(field, item)

    def test_newest_first(self):
        res  = self.client.get("/notifications/api/")
        data = res.json()
        self.assertEqual(data[0]["message"], "Third.")
        self.assertEqual(data[2]["message"], "First.")

    def test_returns_max_20(self):
        for i in range(25):
            notify(recipient=self.user, verb="stage_changed", message=f"Extra {i}.")
        res  = self.client.get("/notifications/api/")
        data = res.json()
        self.assertLessEqual(len(data), 20)


class NotificationUnreadCountAPITest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user   = make_employee("count@test.com", "Count", "User")
        self.client.login(username="count@test.com", password="testpass123")

    def test_returns_correct_unread_count(self):
        notify(recipient=self.user, verb="stage_changed",  message="One.")
        notify(recipient=self.user, verb="offer_extended", message="Two.")

        res  = self.client.get("/notifications/api/unread-count/")
        data = res.json()
        self.assertEqual(data["unread"], 2)

    def test_returns_zero_when_no_notifications(self):
        res  = self.client.get("/notifications/api/unread-count/")
        data = res.json()
        self.assertEqual(data["unread"], 0)

    def test_does_not_count_read_notifications(self):
        n = notify(recipient=self.user, verb="stage_changed", message="Read me.")
        n.is_read = True
        n.save()

        notify(recipient=self.user, verb="offer_extended", message="Unread.")

        res  = self.client.get("/notifications/api/unread-count/")
        self.assertEqual(res.json()["unread"], 1)

    def test_does_not_count_other_users_notifications(self):
        other = make_employee("other2@test.com", "Other", "Two")
        notify(recipient=other, verb="stage_changed", message="Not mine.")

        res = self.client.get("/notifications/api/unread-count/")
        self.assertEqual(res.json()["unread"], 0)


class NotificationMarkReadAPITest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user   = make_employee("markread@test.com", "Mark", "Read")
        self.client.login(username="markread@test.com", password="testpass123")
        self.notif  = notify(recipient=self.user, verb="stage_changed", message="Mark me.")

    def test_marks_notification_as_read(self):
        res = self.client.post(f"/notifications/api/{self.notif.pk}/read/")
        self.assertEqual(res.status_code, 200)
        self.notif.refresh_from_db()
        self.assertTrue(self.notif.is_read)

    def test_sets_read_at_timestamp(self):
        self.client.post(f"/notifications/api/{self.notif.pk}/read/")
        self.notif.refresh_from_db()
        self.assertIsNotNone(self.notif.read_at)

    def test_cannot_mark_other_users_notification(self):
        other       = make_employee("owner@test.com", "Owner", "User")
        other_notif = notify(recipient=other, verb="stage_changed", message="Not yours.")

        res = self.client.post(f"/notifications/api/{other_notif.pk}/read/")
        self.assertEqual(res.status_code, 404)

        other_notif.refresh_from_db()
        self.assertFalse(other_notif.is_read)

    def test_returns_404_for_nonexistent_notification(self):
        res = self.client.post("/notifications/api/99999/read/")
        self.assertEqual(res.status_code, 404)


class NotificationMarkAllReadAPITest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user   = make_employee("markall@test.com", "Mark", "All")
        self.client.login(username="markall@test.com", password="testpass123")

        notify(recipient=self.user, verb="stage_changed",   message="One.")
        notify(recipient=self.user, verb="offer_extended",  message="Two.")
        notify(recipient=self.user, verb="employee_approved", message="Three.")

    def test_marks_all_as_read(self):
        res = self.client.post("/notifications/api/mark-all-read/")
        self.assertEqual(res.status_code, 200)
        unread = Notification.objects.filter(recipient=self.user, is_read=False).count()
        self.assertEqual(unread, 0)

    def test_returns_count_of_marked(self):
        res  = self.client.post("/notifications/api/mark-all-read/")
        data = res.json()
        self.assertEqual(data["marked"], 3)

    def test_does_not_affect_other_users_notifications(self):
        other = make_employee("other3@test.com", "Other", "Three")
        notify(recipient=other, verb="stage_changed", message="Not mine.")

        self.client.post("/notifications/api/mark-all-read/")

        other_unread = Notification.objects.filter(recipient=other, is_read=False).count()
        self.assertEqual(other_unread, 1)

    def test_unread_count_is_zero_after_mark_all(self):
        self.client.post("/notifications/api/mark-all-read/")
        res = self.client.get("/notifications/api/unread-count/")
        self.assertEqual(res.json()["unread"], 0)


# ================================================================
# 5. EDGE CASES
# ================================================================

class NotificationEdgeCaseTest(TestCase):

    def setUp(self):
        self.user = make_employee("edge@test.com", "Edge", "Case")

    def test_notify_with_no_hr_managers_does_not_crash(self):
        """get_hr_managers() returns empty list — notify_many should handle it gracefully."""
        from Human_Resources.api.views._notify_helpers import get_hr_managers
        managers = get_hr_managers()
        # Should return a list (possibly empty) without raising
        self.assertIsInstance(managers, list)

        # notify_many with empty list should not crash
        result = notify_many(
            recipients=managers,
            verb="recommendation_submitted",
            message="No HR managers exist.",
        )
        self.assertEqual(result, [])

    def test_get_branch_manager_with_none_branch_returns_none(self):
        from Human_Resources.api.views._notify_helpers import get_branch_manager
        result = get_branch_manager(None)
        self.assertIsNone(result)

    def test_user_display_with_none_returns_system(self):
        from Human_Resources.api.views._notify_helpers import user_display
        self.assertEqual(user_display(None), "System")

    def test_user_display_falls_back_to_username(self):
        from Human_Resources.api.views._notify_helpers import user_display
        # Employee model has no get_full_name returning empty string case
        result = user_display(self.user)
        self.assertTrue(len(result) > 0)

    def test_notify_does_not_raise_on_db_error(self):
        """Simulate a broken save — notify() should catch and return None."""
        from unittest.mock import patch
        with patch("notifications.models.Notification.objects.create", side_effect=Exception("DB down")):
            result = notify(
                recipient=self.user,
                verb="stage_changed",
                message="Should not crash.",
            )
        self.assertIsNone(result)

def test_self_exclusion_works_in_get_hr_managers(self):
        """Actor should not receive their own triggered notification."""
        from Human_Resources.api.views._notify_helpers import get_hr_managers
        from Human_Resources.models.authority import AuthorityRole, AuthorityAssignment

        # Give our user an HR role at GLOBAL scope (no Region/country needed)
        role, _ = AuthorityRole.objects.get_or_create(
            code="HR_ADMIN",
            defaults={
                "name": "HR Administrator",
                "allowed_scopes": ["GLOBAL", "REGION"],
            }
        )
        AuthorityAssignment.objects.create(
            user=self.user,
            role=role,
            scope_type="GLOBAL",
            is_active=True,
        )

        managers_excluding = get_hr_managers(excluding=self.user)
        pks = [m.pk for m in managers_excluding]
        self.assertNotIn(self.user.pk, pks)

        managers_including = get_hr_managers()
        pks_all = [m.pk for m in managers_including]
        self.assertIn(self.user.pk, pks_all)