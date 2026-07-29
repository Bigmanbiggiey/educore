import uuid

from django.test import TestCase

from apps.admissions.models import Application, ApplicationStage, Offer
from apps.core.context import bind_institution
from apps.institutions.models import Institution


class AdmissionsTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)

    def _application(self, **kwargs):
        defaults = {
            "institution_id": self.institution.id,
            "applicant_details": {"first_name": "Amina"},
            "term_applying_for_id": uuid.uuid4(),
        }
        defaults.update(kwargs)
        return Application.objects.create(**defaults)


class ApplicationTests(AdmissionsTestCase):
    def test_defaults_to_submitted_stage(self):
        application = self._application()
        self.assertEqual(application.stage, Application.Stage.SUBMITTED)

    def test_applicant_details_defaults_to_empty_dict(self):
        application = Application.objects.create(
            institution_id=self.institution.id, term_applying_for_id=uuid.uuid4()
        )
        self.assertEqual(application.applicant_details, {})


class ApplicationStageTests(AdmissionsTestCase):
    def test_can_have_multiple_history_rows(self):
        application = self._application()
        ApplicationStage.objects.create(
            institution_id=self.institution.id,
            application=application,
            stage=Application.Stage.SUBMITTED,
        )
        ApplicationStage.objects.create(
            institution_id=self.institution.id,
            application=application,
            stage=Application.Stage.OFFERED,
        )
        self.assertEqual(application.stage_history.count(), 2)


class OfferTests(AdmissionsTestCase):
    def test_an_application_can_have_multiple_offers(self):
        application = self._application()
        Offer.objects.create(
            institution_id=self.institution.id,
            application=application,
            offered_at="2026-01-01T00:00:00Z",
        )
        Offer.objects.create(
            institution_id=self.institution.id,
            application=application,
            offered_at="2026-02-01T00:00:00Z",
        )  # must not raise — re-offers are allowed, no uniqueness constraint
        self.assertEqual(application.offers.count(), 2)
