import uuid

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.communication.models import MessageThread, MessageThreadParticipant
from apps.core.context import bind_institution
from apps.institutions.models import Domain, Institution
from apps.permissions.models import (
    InstitutionMembership,
    MembershipRole,
    Permission,
    Role,
    RolePermission,
)

HOSTNAME = "st-mary.educore.africa"


class CommunicationAPITestCase(APITestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        Domain.objects.create(
            institution=self.institution,
            hostname=HOSTNAME,
            domain_type=Domain.DomainType.SUBDOMAIN,
            is_primary=True,
        )
        self.user = User.objects.create_user(email="user@stmary.ac.ke", password="x" * 12)
        self.membership = InstitutionMembership.objects.create(
            user=self.user, institution=self.institution
        )
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(self.user))

    def _bearer(self, user):
        return f"Bearer {RefreshToken.for_user(user).access_token}"

    def _grant(self, code, user=None, role_name=None):
        membership = self.membership
        if user is not None and user is not self.user:
            membership, _ = InstitutionMembership.objects.get_or_create(
                user=user, institution=self.institution
            )
        role = Role.objects.create(
            name=role_name or f"Test Role — {code}", institution=self.institution
        )
        permission, _ = Permission.objects.get_or_create(code=code)
        RolePermission.objects.create(role=role, permission=permission)
        MembershipRole.objects.create(membership=membership, role=role)
        return role


class AnnouncementViewSetTests(CommunicationAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:communication:announcement-list")

    def _payload(self, **overrides):
        payload = {
            "kind": "announcement",
            "title": "Sports Day",
            "body": "Sports day is next Friday.",
            "audience": {},
            "channels": [],
        }
        payload.update(overrides)
        return payload

    def test_create_without_permission_is_denied(self):
        response = self.client.post(self.url, self._payload(), format="json", HTTP_HOST=HOSTNAME)
        self.assertEqual(response.status_code, 403)

    def test_create_with_no_published_at_is_a_draft(self):
        self._grant("communication.announcement.manage")

        response = self.client.post(self.url, self._payload(), format="json", HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "draft")

    def test_read_requires_view_permission(self):
        self._grant("communication.announcement.manage")
        self.client.post(self.url, self._payload(), format="json", HTTP_HOST=HOSTNAME)

        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 403)

    def test_publish_action_publishes_a_draft(self):
        self._grant("communication.announcement.manage")
        create_response = self.client.post(
            self.url, self._payload(), format="json", HTTP_HOST=HOSTNAME
        )
        publish_url = reverse(
            "v1:communication:announcement-publish", kwargs={"pk": create_response.data["id"]}
        )

        response = self.client.post(publish_url, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "published")

    def test_publishing_an_already_published_announcement_is_rejected(self):
        self._grant("communication.announcement.manage")
        create_response = self.client.post(
            self.url, self._payload(), format="json", HTTP_HOST=HOSTNAME
        )
        publish_url = reverse(
            "v1:communication:announcement-publish", kwargs={"pk": create_response.data["id"]}
        )
        self.client.post(publish_url, HTTP_HOST=HOSTNAME)

        response = self.client.post(publish_url, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 400)


class MessageThreadViewSetTests(CommunicationAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:communication:message-thread-list")

    def test_create_without_permission_is_denied(self):
        response = self.client.post(
            self.url,
            {"participant_user_ids": [str(uuid.uuid4())]},
            format="json",
            HTTP_HOST=HOSTNAME,
        )
        self.assertEqual(response.status_code, 403)

    def test_create_adds_the_creator_as_a_participant(self):
        self._grant("communication.message.create")
        other_user_id = uuid.uuid4()

        response = self.client.post(
            self.url,
            {"participant_user_ids": [str(other_user_id)]},
            format="json",
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)
        with bind_institution(self.institution):
            participant_ids = set(
                MessageThreadParticipant.objects.filter(
                    thread_id=response.data["id"]
                ).values_list("user_id", flat=True)
            )
        self.assertEqual(participant_ids, {self.user.id, other_user_id})

    def test_list_only_shows_threads_the_user_participates_in(self):
        self._grant("communication.message.create")
        with bind_institution(self.institution):
            own_thread = MessageThread.objects.create(institution_id=self.institution.id)
            MessageThreadParticipant.objects.create(
                institution_id=self.institution.id, thread=own_thread, user_id=self.user.id
            )
            other_thread = MessageThread.objects.create(institution_id=self.institution.id)
            MessageThreadParticipant.objects.create(
                institution_id=self.institution.id, thread=other_thread, user_id=uuid.uuid4()
            )

        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 200)
        ids = {row["id"] for row in response.data["results"]}
        self.assertEqual(ids, {str(own_thread.id)})


class MessageViewSetTests(CommunicationAPITestCase):
    def setUp(self):
        super().setUp()
        with bind_institution(self.institution):
            self.thread = MessageThread.objects.create(institution_id=self.institution.id)
            MessageThreadParticipant.objects.create(
                institution_id=self.institution.id, thread=self.thread, user_id=self.user.id
            )
        self.url = reverse(
            "v1:communication:message-thread-messages", kwargs={"thread_pk": self.thread.id}
        )

    def test_participant_can_send_and_list_messages(self):
        response = self.client.post(
            self.url, {"body": "Hello there"}, format="json", HTTP_HOST=HOSTNAME
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["sender_id"], str(self.user.id))

        list_response = self.client.get(self.url, HTTP_HOST=HOSTNAME)
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.data["count"], 1)

    def test_non_participant_cannot_send_a_message(self):
        other_user = User.objects.create_user(email="other@stmary.ac.ke", password="x" * 12)
        InstitutionMembership.objects.create(user=other_user, institution=self.institution)
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(other_user))

        response = self.client.post(
            self.url, {"body": "Sneaky"}, format="json", HTTP_HOST=HOSTNAME
        )

        self.assertEqual(response.status_code, 403)

    def test_non_participant_cannot_list_messages(self):
        other_user = User.objects.create_user(email="other@stmary.ac.ke", password="x" * 12)
        InstitutionMembership.objects.create(user=other_user, institution=self.institution)
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(other_user))

        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 403)
