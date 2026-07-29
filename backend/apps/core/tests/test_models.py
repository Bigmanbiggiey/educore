"""Tests for docs/multitenancy.md §3's core safety mechanism: the
tenant-scoped auto-filtering manager must fail loudly with no tenant bound,
and must never leak rows across tenants.
"""

import uuid
from types import SimpleNamespace

from django.db import connection, models
from django.test import TestCase
from django.test.utils import isolate_apps

from apps.core.context import TenantContextMissing, bind_institution
from apps.core.models import TenantScopedSoftDeleteModel


def _institution():
    return SimpleNamespace(id=uuid.uuid4())


@isolate_apps("apps.core")
class TenantScopedSoftDeleteModelTests(TestCase):
    """Exercises TenantScopedModel + SoftDeleteModel behavior together via
    TenantScopedSoftDeleteModel, since that's the composed base every
    soft-deletable Layer 1 model (Student, Invoice, ...) will actually use.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        class Widget(TenantScopedSoftDeleteModel):
            name = models.CharField(max_length=50)

            class Meta:
                app_label = "core"

        cls.Widget = Widget
        with connection.schema_editor() as editor:
            editor.create_model(Widget)

    @classmethod
    def tearDownClass(cls):
        with connection.schema_editor() as editor:
            editor.delete_model(cls.Widget)
        super().tearDownClass()

    def test_query_without_bound_tenant_raises(self):
        with self.assertRaises(TenantContextMissing):
            list(self.Widget.objects.all())

    def test_none_works_without_a_bound_tenant(self):
        """`.none()` never touches real data (Django's EmptyQuerySet
        short-circuits before hitting the DB), so third-party
        schema-introspection tooling (drf-spectacular, django-filter) that
        calls `Model._default_manager.none()` outside any real request
        must not be met with TenantContextMissing."""
        self.assertEqual(list(self.Widget.objects.none()), [])

    def test_default_manager_only_sees_the_bound_tenant(self):
        institution_a, institution_b = _institution(), _institution()
        with bind_institution(institution_a):
            self.Widget.objects.create(institution_id=institution_a.id, name="a")
        with bind_institution(institution_b):
            self.Widget.objects.create(institution_id=institution_b.id, name="b")

        with bind_institution(institution_a):
            names = list(self.Widget.objects.values_list("name", flat=True))
        self.assertEqual(names, ["a"])

    def test_default_manager_excludes_soft_deleted_rows(self):
        institution = _institution()
        with bind_institution(institution):
            widget = self.Widget.objects.create(institution_id=institution.id, name="x")
            widget.delete()
            self.assertEqual(list(self.Widget.objects.all()), [])
            self.assertTrue(self.Widget.all_objects.filter(pk=widget.pk).exists())

    def test_all_objects_still_respects_tenant_scope(self):
        institution_a, institution_b = _institution(), _institution()
        with bind_institution(institution_a):
            widget = self.Widget.objects.create(institution_id=institution_a.id, name="a")
            widget.delete()

        with bind_institution(institution_b):
            self.assertEqual(list(self.Widget.all_objects.all()), [])
        with bind_institution(institution_a):
            self.assertEqual(list(self.Widget.all_objects.all()), [widget])

    def test_all_tenants_unsafe_ignores_tenant_scope_entirely(self):
        institution_a, institution_b = _institution(), _institution()
        with bind_institution(institution_a):
            self.Widget.objects.create(institution_id=institution_a.id, name="a")
        with bind_institution(institution_b):
            self.Widget.objects.create(institution_id=institution_b.id, name="b")

        self.assertEqual(self.Widget.all_tenants_unsafe.count(), 2)

    def test_hard_delete_actually_removes_the_row(self):
        institution = _institution()
        with bind_institution(institution):
            widget = self.Widget.objects.create(institution_id=institution.id, name="x")
            widget.hard_delete()
            self.assertFalse(self.Widget.all_tenants_unsafe.filter(pk=widget.pk).exists())

    def test_carries_timestamps(self):
        """docs/database.md §1: created_at/updated_at are "not optional
        per-model" — TenantScopedModel extends TimeStampedModel precisely
        so every Layer 1+ app gets these for free."""
        institution = _institution()
        with bind_institution(institution):
            widget = self.Widget.objects.create(institution_id=institution.id, name="x")
        self.assertIsNotNone(widget.created_at)
        self.assertIsNotNone(widget.updated_at)
