from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.institutions.models import Domain, Institution, InstitutionCurriculum


class InstitutionConstraintTests(TestCase):
    def test_dedicated_db_tier_requires_a_db_alias(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Institution.objects.create(
                    name="Enterprise School",
                    slug="enterprise-school",
                    isolation_tier=Institution.IsolationTier.DEDICATED_DB,
                    db_alias="",
                )

    def test_dedicated_db_tier_with_a_db_alias_is_allowed(self):
        institution = Institution.objects.create(
            name="Enterprise School",
            slug="enterprise-school",
            isolation_tier=Institution.IsolationTier.DEDICATED_DB,
            db_alias="enterprise_school",
        )
        self.assertEqual(institution.db_alias, "enterprise_school")


class DomainConstraintTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")

    def test_only_one_primary_domain_per_institution(self):
        Domain.objects.create(
            institution=self.institution,
            hostname="st-mary.educore.africa",
            domain_type=Domain.DomainType.SUBDOMAIN,
            is_primary=True,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Domain.objects.create(
                    institution=self.institution,
                    hostname="portal.stmary.sc.ke",
                    domain_type=Domain.DomainType.CUSTOM,
                    is_primary=True,
                )

    def test_a_second_non_primary_domain_is_allowed(self):
        Domain.objects.create(
            institution=self.institution,
            hostname="st-mary.educore.africa",
            domain_type=Domain.DomainType.SUBDOMAIN,
            is_primary=True,
        )
        Domain.objects.create(
            institution=self.institution,
            hostname="portal.stmary.sc.ke",
            domain_type=Domain.DomainType.CUSTOM,
            is_primary=False,
        )
        self.assertEqual(self.institution.domains.count(), 2)

    def test_hostname_is_globally_unique(self):
        Domain.objects.create(
            institution=self.institution,
            hostname="st-mary.educore.africa",
            domain_type=Domain.DomainType.SUBDOMAIN,
            is_primary=True,
        )
        other = Institution.objects.create(name="Other School", slug="other-school")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Domain.objects.create(
                    institution=other,
                    hostname="st-mary.educore.africa",
                    domain_type=Domain.DomainType.SUBDOMAIN,
                    is_primary=False,
                )


class InstitutionCurriculumConstraintTests(TestCase):
    def test_a_curriculum_type_cannot_be_attached_twice(self):
        institution = Institution.objects.create(name="St Mary", slug="st-mary")
        InstitutionCurriculum.objects.create(
            institution=institution, curriculum_type=InstitutionCurriculum.CurriculumType.CBC
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InstitutionCurriculum.objects.create(
                    institution=institution,
                    curriculum_type=InstitutionCurriculum.CurriculumType.CBC,
                )

    def test_an_institution_can_run_more_than_one_curriculum(self):
        institution = Institution.objects.create(name="St Mary", slug="st-mary")
        InstitutionCurriculum.objects.create(
            institution=institution, curriculum_type=InstitutionCurriculum.CurriculumType.CBC
        )
        InstitutionCurriculum.objects.create(
            institution=institution,
            curriculum_type=InstitutionCurriculum.CurriculumType.EIGHT_FOUR_FOUR,
        )
        self.assertEqual(institution.curricula.count(), 2)
