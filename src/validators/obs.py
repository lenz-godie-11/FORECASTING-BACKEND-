from datetime import date

from rest_framework import serializers


class ObservationSerializer(serializers.Serializer):
    """Validates a single observation payload."""

    date = serializers.DateField()
    patients = serializers.IntegerField(min_value=0)
    source = serializers.CharField(
        max_length=100,
        required=False,
        default="hospital_system",
    )

    def validate_date(self, value):
        if value > date.today():
            raise serializers.ValidationError(
                "Observation date cannot be in the future."
            )

        return value
