from rest_framework import serializers

class GoogleLoginSerializer(serializers.Serializer):
    token = serializers.CharField(
        required=True, 
        allow_blank=False,
        help_text="The ID Token (JWT) returned by Google Sign-In button."
    )
