"""Registers `CBCEngine` into `academics`' curriculum registry on app
load — the sanctioned Layer 2 -> `academics` import direction
(docs/modules.md); `academics` never imports back.
"""

from django.apps import AppConfig


class CurriculumCbcConfig(AppConfig):
    name = "apps.curriculum_cbc"

    def ready(self):
        from apps.academics import registry
        from apps.curriculum_cbc.engine import CBCEngine
        from apps.institutions.models import InstitutionCurriculum

        registry.register(InstitutionCurriculum.CurriculumType.CBC, CBCEngine)
