from django.test import TestCase

from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.audit.services import log_action
from apps.institutions.models import Institution


class LogActionTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.actor = User.objects.create_user(email="admin@stmary.ac.ke", password="x" * 12)

    def test_logs_an_action_with_a_target_and_diff(self):
        log = log_action(
            actor=self.actor,
            institution=self.institution,
            action="institutions.institution.provision",
            target=self.institution,
            diff={"before": None, "after": {"name": "St Mary"}},
            ip_address="41.90.64.1",
        )

        self.assertEqual(log.actor, self.actor)
        self.assertEqual(log.institution, self.institution)
        self.assertEqual(log.target, self.institution)
        self.assertEqual(log.diff, {"before": None, "after": {"name": "St Mary"}})
        self.assertEqual(log.ip_address, "41.90.64.1")

    def test_logs_an_action_with_no_target(self):
        log = log_action(
            actor=None, institution=None, action="platform.tenant.list", target=None
        )

        self.assertIsNone(log.target_content_type)
        self.assertIsNone(log.target_object_id)

    def test_diff_defaults_to_an_empty_dict(self):
        log = log_action(actor=self.actor, institution=self.institution, action="some.action")

        self.assertEqual(log.diff, {})

    def test_persists_to_the_database(self):
        log_action(actor=self.actor, institution=self.institution, action="some.action")

        self.assertEqual(AuditLog.objects.count(), 1)
