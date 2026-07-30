"""Registers `BritishEngine` into `academics`' curriculum registry on app
load — same self-registration pattern as `curriculum_cbc`/`curriculum_844`.
"""

from django.apps import AppConfig


class CurriculumBritishConfig(AppConfig):
    name = "apps.curriculum_british"

    def ready(self):
        from apps.academics import registry
        from apps.curriculum_british.engine import BritishEngine
        from apps.institutions.models import InstitutionCurriculum

        registry.register(InstitutionCurriculum.CurriculumType.BRITISH, BritishEngine)
