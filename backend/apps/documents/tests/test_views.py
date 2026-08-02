from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.institutions.models import Domain, Institution
from apps.permissions.models import (
    InstitutionMembership,
    MembershipRole,
    Permission,
    Role,
    RolePermission,
)

HOSTNAME = "st-mary.educore.africa"


class DocumentsAPITestCase(APITestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        Domain.objects.create(
            institution=self.institution,
            hostname=HOSTNAME,
            domain_type=Domain.DomainType.SUBDOMAIN,
            is_primary=True,
        )
        self.user = User.objects.create_user(email="registrar@stmary.ac.ke", password="x" * 12)
        self.membership = InstitutionMembership.objects.create(
            user=self.user, institution=self.institution
        )
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(self.user))
        self.content_type_id = ContentType.objects.get_for_model(Institution).id

    def _bearer(self, user):
        return f"Bearer {RefreshToken.for_user(user).access_token}"

    def _grant(self, code):
        role = Role.objects.create(name="Test Role", institution=self.institution)
        permission = Permission.objects.create(code=code)
        RolePermission.objects.create(role=role, permission=permission)
        MembershipRole.objects.create(membership=self.membership, role=role)


class DocumentViewSetTests(DocumentsAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:documents:document-list")
        self.payload = {
            "minio_object_key": "reports/transcript.pdf",
            "target_content_type": self.content_type_id,
            "target_object_id": str(self.institution.id),
        }

    def test_create_without_permission_is_denied(self):
        response = self.client.post(self.url, self.payload, HTTP_HOST=HOSTNAME)
        self.assertEqual(response.status_code, 403)

    def test_create_with_permission_succeeds(self):
        self._grant("documents.document.manage")

        response = self.client.post(self.url, self.payload, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["minio_object_key"], "reports/transcript.pdf")

    def test_reads_are_open_to_any_active_member(self):
        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)
        self.assertEqual(response.status_code, 200)

    def test_soft_deleted_documents_disappear_from_the_list(self):
        self._grant("documents.document.manage")
        create_response = self.client.post(self.url, self.payload, HTTP_HOST=HOSTNAME)
        doc_id = create_response.data["id"]

        delete_response = self.client.delete(
            reverse("v1:documents:document-detail", kwargs={"pk": doc_id}), HTTP_HOST=HOSTNAME
        )
        list_response = self.client.get(self.url, HTTP_HOST=HOSTNAME)

        self.assertEqual(delete_response.status_code, 204)
        self.assertEqual(list_response.data["count"], 0)

    def test_filter_by_is_confidential(self):
        self._grant("documents.document.manage")
        self.client.post(self.url, self.payload, HTTP_HOST=HOSTNAME)
        self.client.post(
            self.url, {**self.payload, "is_confidential": True}, HTTP_HOST=HOSTNAME
        )

        response = self.client.get(self.url, {"is_confidential": "true"}, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)


class DocumentCategoryViewSetTests(DocumentsAPITestCase):
    def test_create_requires_permission(self):
        response = self.client.post(
            reverse("v1:documents:document-category-list"),
            {"name": "Transcripts"},
            HTTP_HOST=HOSTNAME,
        )
        self.assertEqual(response.status_code, 403)
