import uuid

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.communication.models import MessageThread, MessageThreadParticipant
from apps.core.context import bind_institution
from apps.institutions.models import Institution


class CommunicationModelTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)


class MessageThreadParticipantConstraintTests(CommunicationModelTestCase):
    def test_unique_per_thread_and_user(self):
        thread = MessageThread.objects.create(institution_id=self.institution.id)
        user_id = uuid.uuid4()
        MessageThreadParticipant.objects.create(
            institution_id=self.institution.id, thread=thread, user_id=user_id
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                MessageThreadParticipant.objects.create(
                    institution_id=self.institution.id, thread=thread, user_id=user_id
                )

    def test_same_user_in_a_different_thread_is_allowed(self):
        thread_one = MessageThread.objects.create(institution_id=self.institution.id)
        thread_two = MessageThread.objects.create(institution_id=self.institution.id)
        user_id = uuid.uuid4()
        MessageThreadParticipant.objects.create(
            institution_id=self.institution.id, thread=thread_one, user_id=user_id
        )

        MessageThreadParticipant.objects.create(
            institution_id=self.institution.id, thread=thread_two, user_id=user_id
        )  # must not raise
