"""Registers `EightFourFourEngine` into `academics`' curriculum registry on
app load — same self-registration pattern as `curriculum_cbc/apps.py`.
"""

from django.apps import AppConfig


class Curriculum844Config(AppConfig):
    name = "apps.curriculum_844"

    def ready(self):
        from apps.academics import registry
        from apps.curriculum_844.engine import EightFourFourEngine
        from apps.institutions.models import InstitutionCurriculum

        registry.register(InstitutionCurriculum.CurriculumType.EIGHT_FOUR_FOUR, EightFourFourEngine)
