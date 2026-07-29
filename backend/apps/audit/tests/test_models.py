from django.test import TestCase

from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.institutions.models import Institution


class AuditLogAppendOnlyTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.actor = User.objects.create_user(email="admin@stmary.ac.ke", password="x" * 12)
        self.log = AuditLog.objects.create(
            actor=self.actor,
            institution=self.institution,
            action="institutions.institution.provision",
        )

    def test_saving_an_existing_row_is_rejected(self):
        self.log.action = "tampered"
        with self.assertRaises(ValueError):
            self.log.save()

    def test_deleting_an_instance_is_rejected(self):
        with self.assertRaises(ValueError):
            self.log.delete()

    def test_queryset_update_is_rejected(self):
        with self.assertRaises(ValueError):
            AuditLog.objects.filter(pk=self.log.pk).update(action="tampered")

    def test_queryset_delete_is_rejected(self):
        with self.assertRaises(ValueError):
            AuditLog.objects.filter(pk=self.log.pk).delete()

    def test_row_survives_institution_deletion(self):
        self.institution.delete()

        self.log.refresh_from_db()
        self.assertIsNone(self.log.institution)

    def test_row_survives_actor_deletion(self):
        self.actor.delete()

        self.log.refresh_from_db()
        self.assertIsNone(self.log.actor)


class AuditLogNullableFieldTests(TestCase):
    def test_platform_level_action_has_no_institution(self):
        log = AuditLog.objects.create(actor=None, institution=None, action="platform.tenant.list")
        self.assertIsNone(log.institution)

    def test_system_initiated_action_has_no_actor(self):
        institution = Institution.objects.create(name="St Mary", slug="st-mary")
        log = AuditLog.objects.create(
            actor=None, institution=institution, action="notifications.digest.send"
        )
        self.assertIsNone(log.actor)
