from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
        ]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

from rest_framework_simplejwt.tokens import RefreshToken

class LoginSerializer(serializers.Serializer):
    username_or_email = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username_or_email = attrs.get("username_or_email")
        password = attrs.get("password")

        user = User.objects.filter(
            username=username_or_email
        ).first()

        if not user:
            user = user.objects.filter(
                email__iexact=username_or_email
            ).first()

        if not user or not user.check_password(password):
            raise serializers.ValiadationError(
                "Invalid username/email or password."
            )

        if not user.is_active:
            raise serializers.ValiadationError(
                "This account is inactive."
            )


        refresh = RefreshToken.for_user(user)

        attrs["user"] = user
        attrs["refresh"] = str(refresh)
        attrs["access"] = str(refresh.access_token)

        return attrs