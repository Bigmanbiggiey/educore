from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from apps.core.context import bind_institution
from apps.documents.models import Document
from apps.institutions.models import Institution


class DocumentSoftDeleteTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)

    def test_delete_soft_deletes_rather_than_removing_the_row(self):
        doc = Document.objects.create(
            institution_id=self.institution.id,
            minio_object_key="reports/123.pdf",
            target_content_type=ContentType.objects.get_for_model(Institution),
            target_object_id=self.institution.id,
        )

        doc.delete()

        self.assertFalse(Document.objects.filter(pk=doc.pk).exists())
        self.assertTrue(Document.all_objects.filter(pk=doc.pk).exists())
        self.assertIsNotNone(Document.all_objects.get(pk=doc.pk).deleted_at)
