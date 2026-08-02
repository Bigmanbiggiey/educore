from django.test import TestCase

from apps.documents.selectors import get_documents_for
from apps.documents.services import attach
from apps.institutions.models import Institution


class GetDocumentsForTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.other_institution = Institution.objects.create(name="Other", slug="other")

    def test_returns_only_documents_attached_to_the_target(self):
        document = attach(
            institution=self.institution,
            minio_object_key="reports/a.pdf",
            target=self.institution,
        )
        attach(
            institution=self.institution,
            minio_object_key="reports/b.pdf",
            target=self.other_institution,
        )

        results = get_documents_for(self.institution, self.institution)

        self.assertEqual(results, [document])
