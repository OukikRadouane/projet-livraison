from rest_framework import serializers
from django.db import IntegrityError
from django.contrib.auth.password_validation import validate_password

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "cne",
            "role",
            "capacity_kg",
        ]


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=User.Roles.choices)
    username = serializers.CharField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    cne = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "role",
            "first_name",
            "last_name",
            "phone",
            "cne",
        ]
        extra_kwargs = {
            "email": {"required": True},
            "first_name": {"required": False},
            "last_name": {"required": False},
            "phone": {"required": False},
            "cne": {"required": False},
        }

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        # Normalize and prepare username from email if missing
        email = (attrs.get("email") or "").strip()
        username = (attrs.get("username") or email).strip()
        attrs["email"] = email
        attrs["username"] = username

        # Check for duplicate username
        if username:
            from .models import User
            if User.objects.filter(username=username).exists():
                raise serializers.ValidationError({
                    "email": "Un compte avec cet email existe déjà."
                })

        role = attrs.get("role", User.Roles.CUSTOMER)
        if role == User.Roles.COURIER:
            attrs["capacity_kg"] = 10
        else:
            attrs["capacity_kg"] = 0
            
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        role = validated_data.get("role", User.Roles.CUSTOMER)
        username = validated_data.get("username") or validated_data.get("email")
        validated_data["username"] = username
        if role == User.Roles.COURIER:
            capacity = validated_data.get("capacity_kg", 10)
            if capacity > 10:
                raise serializers.ValidationError({"capacity_kg": "La capacité maximale est de 10 kg."})
            validated_data["capacity_kg"] = 10
        else:
            validated_data["capacity_kg"] = 0
        user = User(**validated_data)
        user.set_password(password)
        try:
            user.save()
        except IntegrityError:
            # In case of race condition, surface a friendly error
            raise serializers.ValidationError({
                "email": "Un compte avec cet email existe déjà. Veuillez vous connecter."
            })
        return user
