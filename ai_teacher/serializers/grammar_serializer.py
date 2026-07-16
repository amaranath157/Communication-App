from rest_framework import serializers


class EnglishCorrectionRequestSerializer(serializers.Serializer):
    text = serializers.CharField(
        required=True,
        min_length=2,
        max_length=3000,
        help_text="The English text you want corrected, polished, and explained.",
    )


class CorrectionItemSerializer(serializers.Serializer):
    original    = serializers.CharField()
    correction  = serializers.CharField()
    explanation = serializers.CharField()


class EnglishCorrectionResponseSerializer(serializers.Serializer):
    original_text     = serializers.CharField()
    corrected_text    = serializers.CharField()
    polished_version  = serializers.CharField()
    corrections       = CorrectionItemSerializer(many=True)
    overall_feedback  = serializers.CharField()
    score_out_of_10   = serializers.IntegerField()
    error             = serializers.BooleanField()
