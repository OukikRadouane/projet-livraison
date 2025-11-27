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

        # Friendly validation for duplicate username (we use email as username)
        if username:
            from .models import User  # local import to avoid circulars at import time
            if User.objects.filter(username=username).exists():
                raise serializers.ValidationError({
                    "email": "Un compte avec cet email existe déjà. Veuillez vous connecter."
                })

        role = attrs.get("role", User.Roles.CUSTOMER)
        # For both roles we now require first_name, last_name, phone
        required_common = {
            "first_name": "Le prénom est requis.",
            "last_name": "Le nom est requis.",
            "phone": "Le téléphone est requis.",
        }
        missing_fields = {}
        for field, message in required_common.items():
            value = (attrs.get(field) or "").strip()
            attrs[field] = value
            if not value:
                missing_fields[field] = message
        if role == User.Roles.COURIER:
            missing_fields = {}
            for field, message in {
                "first_name": "Le prénom est requis pour un livreur.",
                "last_name": "Le nom est requis pour un livreur.",
                "phone": "Le téléphone est requis pour un livreur.",
                "cne": "Le CNE est requis pour un livreur.",
            }.items():
                value = (attrs.get(field) or "").strip()
                attrs[field] = value
                if not value:
                    missing_fields[field] = message
            if missing_fields:
                raise serializers.ValidationError(missing_fields)
            attrs["capacity_kg"] = 10
        else:
            # Customer: must have first_name, last_name, phone; CNE optional
            if missing_fields:
                raise serializers.ValidationError(missing_fields)
            attrs["capacity_kg"] = 0
            for field in ("cne",):
                attrs[field] = (attrs.get(field) or "").strip()
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
