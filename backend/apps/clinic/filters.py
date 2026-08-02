"""Explicit filter whitelists for `clinic` — docs/api-design.md §6:
hand-declared, not auto-derived from `Meta.fields` (see
`attendance.filters`'s module docstring for the full explanation this
project reuses everywhere).
"""

import django_filters

from apps.clinic.models import ClinicVisit, HealthRecord, Medication


class HealthRecordFilterSet(django_filters.FilterSet):
    student_id = django_filters.UUIDFilter(field_name="student_id")

    class Meta:
        model = HealthRecord
        fields = ["student_id"]


class ClinicVisitFilterSet(django_filters.FilterSet):
    student_id = django_filters.UUIDFilter(field_name="student_id")
    visit_date = django_filters.DateFilter(field_name="visit_date")

    class Meta:
        model = ClinicVisit
        fields = ["student_id", "visit_date"]


class MedicationFilterSet(django_filters.FilterSet):
    visit = django_filters.UUIDFilter(field_name="visit_id")

    class Meta:
        model = Medication
        fields = ["visit"]
