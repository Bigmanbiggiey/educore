"""Registers `TVETEngine` into `academics`' curriculum registry on app
load — same self-registration pattern as the other three plugins.
"""

from django.apps import AppConfig


class CurriculumTvetConfig(AppConfig):
    name = "apps.curriculum_tvet"

    def ready(self):
        from apps.academics import registry
        from apps.curriculum_tvet.engine import TVETEngine
        from apps.institutions.models import InstitutionCurriculum

        registry.register(InstitutionCurriculum.CurriculumType.TVET, TVETEngine)
