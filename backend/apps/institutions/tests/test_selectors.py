from django.test import TestCase

from apps.institutions.models import Domain, Institution
from apps.institutions.selectors import get_institution_by_domain


class GetInstitutionByDomainTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        Domain.objects.create(
            institution=self.institution,
            hostname="st-mary.educore.africa",
            domain_type=Domain.DomainType.SUBDOMAIN,
            is_primary=True,
        )

    def test_returns_the_institution_for_a_known_hostname(self):
        self.assertEqual(
            get_institution_by_domain("st-mary.educore.africa"), self.institution
        )

    def test_returns_none_for_an_unknown_hostname(self):
        self.assertIsNone(get_institution_by_domain("nope.educore.africa"))

    def test_returns_none_for_an_inactive_institution(self):
        self.institution.is_active = False
        self.institution.save(update_fields=["is_active"])
        self.assertIsNone(get_institution_by_domain("st-mary.educore.africa"))
