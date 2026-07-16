from django.test import TestCase

from apps.institutions.models import Domain, Institution, InstitutionCurriculum
from apps.institutions.services import (
    add_custom_domain,
    provision_institution,
    set_isolation_tier,
    verify_domain,
)


class ProvisionInstitutionTests(TestCase):
    def test_creates_institution_primary_domain_and_curricula_atomically(self):
        institution = provision_institution(
            name="St Mary",
            slug="st-mary",
            curriculum_types=[
                InstitutionCurriculum.CurriculumType.CBC,
                InstitutionCurriculum.CurriculumType.EIGHT_FOUR_FOUR,
            ],
        )

        self.assertEqual(institution.name, "St Mary")
        domain = institution.domains.get()
        self.assertEqual(domain.hostname, "st-mary.educore.africa")
        self.assertTrue(domain.is_primary)
        self.assertIsNotNone(domain.verified_at)
        self.assertEqual(institution.curricula.count(), 2)

    def test_rejects_an_unknown_curriculum_type(self):
        with self.assertRaises(ValueError):
            provision_institution(name="St Mary", slug="st-mary", curriculum_types=["klingon"])
        self.assertFalse(Institution.objects.filter(slug="st-mary").exists())


class SetIsolationTierTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")

    def test_dedicated_db_requires_a_db_alias(self):
        with self.assertRaises(ValueError):
            set_isolation_tier(self.institution, Institution.IsolationTier.DEDICATED_DB)

    def test_setting_dedicated_db_with_an_alias_persists(self):
        set_isolation_tier(
            self.institution, Institution.IsolationTier.DEDICATED_DB, db_alias="st_mary_db"
        )
        self.institution.refresh_from_db()
        self.assertEqual(self.institution.isolation_tier, Institution.IsolationTier.DEDICATED_DB)
        self.assertEqual(self.institution.db_alias, "st_mary_db")

    def test_switching_away_from_dedicated_db_clears_the_alias(self):
        set_isolation_tier(
            self.institution, Institution.IsolationTier.DEDICATED_DB, db_alias="st_mary_db"
        )
        set_isolation_tier(self.institution, Institution.IsolationTier.SHARED_ROW)
        self.institution.refresh_from_db()
        self.assertEqual(self.institution.db_alias, "")

    def test_rejects_an_unknown_tier(self):
        with self.assertRaises(ValueError):
            set_isolation_tier(self.institution, "made_up_tier")


class DomainVerificationTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")

    def test_add_custom_domain_generates_a_verification_token(self):
        domain = add_custom_domain(self.institution, "portal.stmary.sc.ke")
        self.assertEqual(domain.domain_type, Domain.DomainType.CUSTOM)
        self.assertIsNone(domain.verified_at)
        self.assertTrue(domain.verification_token)

    def test_verify_domain_succeeds_when_the_token_is_present(self):
        domain = add_custom_domain(self.institution, "portal.stmary.sc.ke")
        verify_domain(domain, resolved_txt_records=[domain.verification_token, "unrelated-record"])
        domain.refresh_from_db()
        self.assertIsNotNone(domain.verified_at)

    def test_verify_domain_fails_when_the_token_is_absent(self):
        domain = add_custom_domain(self.institution, "portal.stmary.sc.ke")
        with self.assertRaises(ValueError):
            verify_domain(domain, resolved_txt_records=["unrelated-record"])
        domain.refresh_from_db()
        self.assertIsNone(domain.verified_at)
