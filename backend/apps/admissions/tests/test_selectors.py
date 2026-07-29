import uuid

from django.test import TestCase

from apps.admissions.models import Application
from apps.admissions.selectors import get_application, get_applications_by_stage
from apps.core.context import bind_institution
from apps.institutions.models import Institution


class AdmissionsSelectorTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)


class GetApplicationTests(AdmissionsSelectorTestCase):
    def test_returns_the_matching_application(self):
        application = Application.objects.create(
            institution_id=self.institution.id, term_applying_for_id=uuid.uuid4()
        )
        self.assertEqual(get_application(self.institution, application.id), application)

    def test_returns_none_when_no_application_exists(self):
        self.assertIsNone(get_application(self.institution, uuid.uuid4()))


class GetApplicationsByStageTests(AdmissionsSelectorTestCase):
    def test_filters_by_stage(self):
        submitted = Application.objects.create(
            institution_id=self.institution.id,
            term_applying_for_id=uuid.uuid4(),
            stage=Application.Stage.SUBMITTED,
        )
        Application.objects.create(
            institution_id=self.institution.id,
            term_applying_for_id=uuid.uuid4(),
            stage=Application.Stage.REJECTED,
        )

        results = get_applications_by_stage(self.institution, Application.Stage.SUBMITTED)

        self.assertEqual(results, [submitted])
