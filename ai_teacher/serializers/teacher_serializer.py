from rest_framework import serializers

class EvaluationRequestSerializer(serializers.Serializer):
    text = serializers.CharField(required=True, min_length=1, help_text="The English text to be evaluated.")
