"""Request shapes for `reports`'s API surface — docs/api-design.md."""

from rest_framework import serializers


class GenerateReportCardRequestSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    term_id = serializers.UUIDField()


class GenerateClassReportCardsRequestSerializer(serializers.Serializer):
    class_grade_id = serializers.UUIDField()
    term_id = serializers.UUIDField()
