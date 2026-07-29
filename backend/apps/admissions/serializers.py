"""Request/response shapes for `admissions`'s API surface — docs/api-design.md.
`Application.stage` is read-only here — it only ever changes via the
dedicated `make-offer`/`accept-offer`/`convert-to-enrollment` RPC actions,
never an overloaded `PATCH` (§1), same convention `classes_streams.Term.is_current`
established.
"""

from rest_framework import serializers

from api.serializers import TenantScopedModelSerializer
from apps.admissions.models import Application, ApplicationStage, Offer


class ApplicationStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationStage
        fields = ["id", "stage", "note", "created_at"]
        read_only_fields = fields


class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = ["id", "offered_at", "accepted_at", "created_at", "updated_at"]
        read_only_fields = fields


class ApplicationSerializer(TenantScopedModelSerializer):
    stage_history = ApplicationStageSerializer(many=True, read_only=True)
    offers = OfferSerializer(many=True, read_only=True)

    class Meta:
        model = Application
        fields = [
            "id",
            "applicant_details",
            "stage",
            "term_applying_for_id",
            "stage_history",
            "offers",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "stage", "stage_history", "offers", "created_at", "updated_at"]
        extra_kwargs = {
            "applicant_details": {
                "help_text": "Unstructured applicant info (name, DOB, guardian contact, etc)."
            },
            "term_applying_for_id": {
                "help_text": "The term being applied for (classes_streams.Term)."
            },
        }


class ConvertToEnrollmentSerializer(serializers.Serializer):
    admission_number = serializers.CharField(max_length=50)
    class_grade_id = serializers.UUIDField()
    term_id = serializers.UUIDField()
    stream_id = serializers.UUIDField(required=False, allow_null=True)
