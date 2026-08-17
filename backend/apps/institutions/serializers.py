"""Request/response shapes for the platform-staff institution-management
API (docs/permissions.md §7) — thin wrappers around `services.py`'s
already-correct functions, one serializer per function rather than one
big serializer trying to cover every action's different field set.
"""

from rest_framework import serializers

from apps.institutions.models import Domain, Institution, InstitutionCurriculum


class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = [
            "id",
            "name",
            "slug",
            "isolation_tier",
            "db_alias",
            "timezone",
            "logo_url",
            "primary_color",
            "favicon_url",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ProvisionInstitutionSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    slug = serializers.SlugField(max_length=100)
    curriculum_types = serializers.ListField(
        child=serializers.ChoiceField(choices=InstitutionCurriculum.CurriculumType.choices)
    )
    timezone_name = serializers.CharField(max_length=50, required=False, default="Africa/Nairobi")
    # docs/multitenancy.md §7: provisioning always seeds the Institution
    # Administrator — see services.provision_institution's docstring for
    # why that admin is created via a signal, not inline in this app.
    admin_email = serializers.EmailField()
    admin_phone = serializers.CharField(
        max_length=20, required=False, allow_null=True, allow_blank=True, default=None
    )


class SetIsolationTierSerializer(serializers.Serializer):
    tier = serializers.ChoiceField(choices=Institution.IsolationTier.choices)
    db_alias = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = [
            "id",
            "institution",
            "hostname",
            "domain_type",
            "is_primary",
            "verification_token",
            "verified_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class AddCustomDomainSerializer(serializers.Serializer):
    hostname = serializers.CharField(max_length=255)


class VerifyDomainSerializer(serializers.Serializer):
    # The real DNS lookup is an explicitly-deferred Celery task
    # (services.verify_domain's own docstring) — this takes the
    # already-resolved records as input rather than performing the lookup
    # itself.
    resolved_txt_records = serializers.ListField(child=serializers.CharField())
