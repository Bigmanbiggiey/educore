"""Registers `UniversityEngine` into `academics`' curriculum registry on
app load — same self-registration pattern as the other four plugins.
"""

from django.apps import AppConfig


class CurriculumUniversityConfig(AppConfig):
    name = "apps.curriculum_university"

    def ready(self):
        from apps.academics import registry
        from apps.curriculum_university.engine import UniversityEngine
        from apps.institutions.models import InstitutionCurriculum

        registry.register(InstitutionCurriculum.CurriculumType.UNIVERSITY, UniversityEngine)
