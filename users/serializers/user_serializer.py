from rest_framework import serializers

class UserUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    phone = serializers.CharField(max_length=20, required=False)
    gender = serializers.CharField(max_length=1, required=False)
    age = serializers.IntegerField(required=False)
    bio = serializers.CharField(required=False)
    country = serializers.CharField(max_length=100, required=False)
    profile_photo = serializers.URLField(required=False)
    is_online = serializers.BooleanField(required=False)
