import uuid

from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.communication.models import Announcement, MessageThreadParticipant
from apps.communication.services import (
    create_announcement,
    create_thread,
    publish_announcement,
    send_message,
)
from apps.communication.tasks import publish_due_announcements
from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.notifications_core.models import NotificationLog
from apps.permissions.models import InstitutionMembership, MembershipRole, Role
from apps.students.models import Enrollment, GuardianRelationship, Student


class CommunicationServiceTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")


class CreateAnnouncementTests(CommunicationServiceTestCase):
    def test_no_published_at_is_a_draft(self):
        announcement = create_announcement(
            institution=self.institution,
            kind=Announcement.Kind.ANNOUNCEMENT,
            title="Sports Day",
            body="Sports day is next Friday.",
            audience={},
            channels=[],
            created_by_id=uuid.uuid4(),
        )

        self.assertEqual(announcement.status, Announcement.Status.DRAFT)
        self.assertIsNone(announcement.published_at)

    def test_future_published_at_is_scheduled(self):
        future = timezone.now() + timezone.timedelta(days=1)

        announcement = create_announcement(
            institution=self.institution,
            kind=Announcement.Kind.CIRCULAR,
            title="Term Fees",
            body="Fees are due next week.",
            audience={},
            channels=[],
            created_by_id=uuid.uuid4(),
            published_at=future,
        )

        self.assertEqual(announcement.status, Announcement.Status.SCHEDULED)
        self.assertEqual(announcement.published_at, future)

    def test_past_published_at_publishes_immediately(self):
        past = timezone.now() - timezone.timedelta(minutes=5)

        announcement = create_announcement(
            institution=self.institution,
            kind=Announcement.Kind.ANNOUNCEMENT,
            title="Closure",
            body="School is closed tomorrow.",
            audience={},
            channels=[],
            created_by_id=uuid.uuid4(),
            published_at=past,
        )

        self.assertEqual(announcement.status, Announcement.Status.PUBLISHED)
        self.assertIsNotNone(announcement.published_at)


class PublishAnnouncementAudienceTests(CommunicationServiceTestCase):
    def _announcement(self, audience, channels=None):
        with bind_institution(self.institution):
            return Announcement.objects.create(
                institution_id=self.institution.id,
                kind=Announcement.Kind.ANNOUNCEMENT,
                title="Test",
                body="Body",
                audience=audience,
                channels=channels or ["email"],
            )

    def test_resolves_role_based_audience(self):
        teacher = User.objects.create_user(email="teacher@stmary.ac.ke", password="x" * 12)
        membership = InstitutionMembership.objects.create(
            user=teacher, institution=self.institution
        )
        role = Role.objects.create(name="Teacher", institution=self.institution)
        MembershipRole.objects.create(membership=membership, role=role)
        announcement = self._announcement({"roles": ["Teacher"]})

        publish_announcement(institution=self.institution, announcement=announcement)

        self.assertTrue(
            NotificationLog.objects.filter(
                institution=self.institution, recipient_user=teacher, channel="email"
            ).exists()
        )

    def test_resolves_class_based_audience(self):
        with bind_institution(self.institution):
            student = Student.objects.create(
                institution_id=self.institution.id,
                admission_number="ADM-001",
                first_name="Amina",
                last_name="Otieno",
            )
            class_grade_id = uuid.uuid4()
            Enrollment.objects.create(
                institution_id=self.institution.id,
                student=student,
                class_grade_id=class_grade_id,
                term_id=uuid.uuid4(),
                status=Enrollment.Status.ACTIVE,
            )
            guardian = User.objects.create_user(email="parent@stmary.ac.ke", password="x" * 12)
            GuardianRelationship.objects.create(
                institution_id=self.institution.id,
                student=student,
                guardian_user_id=guardian.id,
                relationship_type=GuardianRelationship.RelationshipType.PARENT,
            )
        announcement = self._announcement({"class_grade_ids": [str(class_grade_id)]})

        publish_announcement(institution=self.institution, announcement=announcement)

        self.assertTrue(
            NotificationLog.objects.filter(
                institution=self.institution, recipient_user=guardian, channel="email"
            ).exists()
        )

    def test_deduplicates_a_recipient_matching_both_role_and_class(self):
        with bind_institution(self.institution):
            student = Student.objects.create(
                institution_id=self.institution.id,
                admission_number="ADM-001",
                first_name="Amina",
                last_name="Otieno",
            )
            class_grade_id = uuid.uuid4()
            Enrollment.objects.create(
                institution_id=self.institution.id,
                student=student,
                class_grade_id=class_grade_id,
                term_id=uuid.uuid4(),
                status=Enrollment.Status.ACTIVE,
            )
        guardian_teacher = User.objects.create_user(email="both@stmary.ac.ke", password="x" * 12)
        membership = InstitutionMembership.objects.create(
            user=guardian_teacher, institution=self.institution
        )
        role = Role.objects.create(name="Teacher", institution=self.institution)
        MembershipRole.objects.create(membership=membership, role=role)
        with bind_institution(self.institution):
            GuardianRelationship.objects.create(
                institution_id=self.institution.id,
                student=student,
                guardian_user_id=guardian_teacher.id,
                relationship_type=GuardianRelationship.RelationshipType.PARENT,
            )
        announcement = self._announcement(
            {"roles": ["Teacher"], "class_grade_ids": [str(class_grade_id)]}
        )

        publish_announcement(institution=self.institution, announcement=announcement)

        self.assertEqual(
            NotificationLog.objects.filter(
                institution=self.institution, recipient_user=guardian_teacher
            ).count(),
            1,
        )

    def test_a_recipient_with_no_address_for_the_channel_does_not_abort_the_rest(self):
        # A guardian with no phone on file, targeted by an SMS-channel
        # announcement — notifications_core.services.send raises ValueError
        # for this one recipient/channel; the fan-out must skip it, not
        # crash and leave every other recipient unnotified.
        no_phone_guardian = User.objects.create_user(
            email="nophone@stmary.ac.ke", password="x" * 12
        )
        with_phone_guardian = User.objects.create_user(
            email="withphone@stmary.ac.ke", password="x" * 12, phone="254712345678"
        )
        with bind_institution(self.institution):
            student_one = Student.objects.create(
                institution_id=self.institution.id,
                admission_number="ADM-001",
                first_name="A",
                last_name="One",
            )
            student_two = Student.objects.create(
                institution_id=self.institution.id,
                admission_number="ADM-002",
                first_name="B",
                last_name="Two",
            )
            class_grade_id = uuid.uuid4()
            for student in (student_one, student_two):
                Enrollment.objects.create(
                    institution_id=self.institution.id,
                    student=student,
                    class_grade_id=class_grade_id,
                    term_id=uuid.uuid4(),
                    status=Enrollment.Status.ACTIVE,
                )
            GuardianRelationship.objects.create(
                institution_id=self.institution.id,
                student=student_one,
                guardian_user_id=no_phone_guardian.id,
                relationship_type=GuardianRelationship.RelationshipType.PARENT,
            )
            GuardianRelationship.objects.create(
                institution_id=self.institution.id,
                student=student_two,
                guardian_user_id=with_phone_guardian.id,
                relationship_type=GuardianRelationship.RelationshipType.PARENT,
            )
        announcement = self._announcement(
            {"class_grade_ids": [str(class_grade_id)]}, channels=["sms"]
        )

        result = publish_announcement(institution=self.institution, announcement=announcement)

        self.assertEqual(result.status, Announcement.Status.PUBLISHED)
        self.assertTrue(
            NotificationLog.objects.filter(
                institution=self.institution, recipient_user=with_phone_guardian, channel="sms"
            ).exists()
        )
        self.assertFalse(
            NotificationLog.objects.filter(
                institution=self.institution, recipient_user=no_phone_guardian
            ).exists()
        )

    def test_marks_the_announcement_published(self):
        announcement = self._announcement({})

        result = publish_announcement(institution=self.institution, announcement=announcement)

        self.assertEqual(result.status, Announcement.Status.PUBLISHED)
        self.assertIsNotNone(result.published_at)


class PublishDueAnnouncementsTaskTests(CommunicationServiceTestCase):
    def test_publishes_a_due_scheduled_announcement(self):
        past = timezone.now() - timezone.timedelta(minutes=1)
        with bind_institution(self.institution):
            announcement = Announcement.objects.create(
                institution_id=self.institution.id,
                kind=Announcement.Kind.ANNOUNCEMENT,
                title="Due",
                body="Body",
                audience={},
                channels=[],
                status=Announcement.Status.SCHEDULED,
                published_at=past,
            )

        publish_due_announcements()

        with bind_institution(self.institution):
            announcement.refresh_from_db()
        self.assertEqual(announcement.status, Announcement.Status.PUBLISHED)

    def test_does_not_touch_a_not_yet_due_announcement(self):
        future = timezone.now() + timezone.timedelta(days=1)
        with bind_institution(self.institution):
            announcement = Announcement.objects.create(
                institution_id=self.institution.id,
                kind=Announcement.Kind.ANNOUNCEMENT,
                title="Not due",
                body="Body",
                audience={},
                channels=[],
                status=Announcement.Status.SCHEDULED,
                published_at=future,
            )

        publish_due_announcements()

        with bind_institution(self.institution):
            announcement.refresh_from_db()
        self.assertEqual(announcement.status, Announcement.Status.SCHEDULED)


class ThreadAndMessageTests(CommunicationServiceTestCase):
    def test_create_thread_adds_participants(self):
        user_ids = [uuid.uuid4(), uuid.uuid4()]

        thread = create_thread(institution=self.institution, participant_user_ids=user_ids)

        with bind_institution(self.institution):
            participant_ids = set(
                MessageThreadParticipant.objects.filter(thread=thread).values_list(
                    "user_id", flat=True
                )
            )
        self.assertEqual(participant_ids, set(user_ids))

    def test_send_message_creates_a_message(self):
        thread = create_thread(institution=self.institution, participant_user_ids=[uuid.uuid4()])
        sender_id = uuid.uuid4()

        message = send_message(
            institution=self.institution, thread=thread, sender_id=sender_id, body="Hello"
        )

        self.assertEqual(message.body, "Hello")
        self.assertEqual(message.sender_id, sender_id)
