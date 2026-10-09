from django.contrib.auth import get_user_model
from django.contrib.auth import password_validation
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'password', 'is_adult_confirmed')
        extra_kwargs = {
            'password': {'write_only': True},
            'is_adult_confirmed': {'write_only': True, 'required': True},
        }

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value

    def validate_is_adult_confirmed(self, value):
        if value is not True:
            raise serializers.ValidationError("You must be 18 or over to use WayShare.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            password=validated_data['password'],
            is_adult_confirmed=validated_data['is_adult_confirmed'],
        )
        return user
