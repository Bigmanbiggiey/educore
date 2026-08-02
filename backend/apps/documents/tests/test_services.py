from django.test import TestCase

from apps.documents.services import attach, create_category
from apps.institutions.models import Institution


class DocumentsServiceTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")


class AttachTests(DocumentsServiceTestCase):
    def test_attaches_a_document_to_the_given_target(self):
        document = attach(
            institution=self.institution,
            minio_object_key="reports/transcript.pdf",
            target=self.institution,
        )

        self.assertEqual(document.target_object_id, self.institution.id)
        self.assertEqual(document.target, self.institution)

    def test_attaches_to_a_category_when_given(self):
        category = create_category(institution=self.institution, name="Transcripts")

        document = attach(
            institution=self.institution,
            minio_object_key="reports/transcript.pdf",
            target=self.institution,
            category=category,
        )

        self.assertEqual(document.category, category)
