from django.test import SimpleTestCase

from apps.academics import registry
from apps.academics.contracts import AssessmentEngine, ReportEngine


class _DummyEngine(AssessmentEngine, ReportEngine):
    def record_assessment(self, *, institution, student_id, term_id, details):
        return details

    def compute_result(self, *, institution, student_id, term_id):
        return None

    def generate_report_data(self, *, institution, student_id, term_id):
        return {}


class _IncompleteEngine(AssessmentEngine, ReportEngine):
    """Deliberately missing `compute_result` — proves the registry rejects
    an incomplete plugin via Python's own ABC machinery, no extra
    validation code needed."""

    def record_assessment(self, *, institution, student_id, term_id, details):
        return details

    def generate_report_data(self, *, institution, student_id, term_id):
        return {}


class RegistryTestCase(SimpleTestCase):
    def setUp(self):
        self._saved_registry = dict(registry._registry)
        registry._registry.clear()
        self.addCleanup(self._restore_registry)

    def _restore_registry(self):
        registry._registry.clear()
        registry._registry.update(self._saved_registry)


class RegisterAndResolveTests(RegistryTestCase):
    def test_resolve_returns_an_instance_of_the_registered_class(self):
        registry.register("dummy", _DummyEngine)
        self.assertIsInstance(registry.resolve("dummy"), _DummyEngine)

    def test_resolve_raises_for_an_unregistered_type(self):
        with self.assertRaises(ValueError):
            registry.resolve("nothing-registered-here")

    def test_re_registering_the_same_type_replaces_it(self):
        registry.register("dummy", _DummyEngine)

        class _OtherEngine(_DummyEngine):
            pass

        registry.register("dummy", _OtherEngine)
        self.assertIsInstance(registry.resolve("dummy"), _OtherEngine)

    def test_registering_an_incomplete_engine_fails_at_resolve_time(self):
        registry.register("incomplete", _IncompleteEngine)
        with self.assertRaises(TypeError):
            registry.resolve("incomplete")
