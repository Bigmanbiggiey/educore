"""Shared ModelSerializer base for every Layer 1+ app — works around a
genuine incompatibility between DRF's automatic uniqueness-validator
generation and `TenantScopedModel`'s eager-raising manager
(apps.core.models.TenantManager): building a validator for a
`UniqueConstraint` that has a `condition=` calls
`model._default_manager.filter(constraint.condition)` directly — bypassing
any view-level `get_queryset()` override entirely — which requires a bound
tenant context that doesn't exist outside a real request, e.g. during
`manage.py spectacular`'s schema generation.

Skipped only when no tenant is bound; runs the real, meaningful check
during an actual request, since `TenantMiddleware` always has one bound by
then.
"""

from rest_framework import serializers

from apps.core.context import current_institution


class TenantScopedModelSerializer(serializers.ModelSerializer):
    def get_unique_together_constraints(self, model):
        if current_institution.get() is None:
            return []
        return super().get_unique_together_constraints(model)
