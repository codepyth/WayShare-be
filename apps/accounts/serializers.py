from django.contrib.auth import authenticate, get_user_model
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


class UserLoginSerializer(serializers.Serializer):
    email   = serializers.EmailField(max_length=255)
    password    = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        user = authenticate(
            request=self.context.get('request'),
            email=attrs['email'].lower(),
            password=attrs['password'],
        )
        if user is None or user.suspended_at or user.deleted_at:
            raise serializers.ValidationError("Invalid email or password.")
        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model   = User
        fields  = (
            'id', 'name', 'email', 'phone', 'driver_enabled',
            'phone_verified_at', 'licence_checked_at', 'id_verified_at',
            'last_login',
        )