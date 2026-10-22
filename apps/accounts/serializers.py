import logging
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth import password_validation
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import serializers

User = get_user_model()
logger = logging.getLogger(__name__)


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


class LoginResponseSerializer(serializers.Serializer):
    user        = UserSerializer()
    csrf_token  = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    old_password    = serializers.CharField(write_only=True)
    new_password    = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        if not self.context['request'].user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value):
        password_validation.validate_password(value, user=self.context['request'].user)
        return value

    def validate(self, attrs):
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError(
                {'new_password': "New password must be different from the current one."}
            )
        return attrs


class PasswordResetSerializer(serializers.Serializer):
    email   = serializers.EmailField()

    def save(self):
        # Email only an account that could log in. The view answers the same either way.
        user = User.objects.filter(
            email=self.validated_data['email'].lower(),
            is_active=True, suspended_at__isnull=True, deleted_at__isnull=True,
        ).first()
        if user is None:
            return

        uid     = urlsafe_base64_encode(force_bytes(user.pk))
        token   = default_token_generator.make_token(user)
        link    = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"
        try:
            send_mail(
                subject="Reset your WayShare password",
                message=(
                    f"Hi {user.name},\n\n"
                    f"Use this link to choose a new password. It expires in 1 hour and works once:\n\n"
                    f"{link}\n\n"
                    f"If you didn't ask for this, ignore this email. Your password won't change.\n"
                ),
                from_email=None,   # DEFAULT_FROM_EMAIL
                recipient_list=[user.email],
            )
        except Exception:
            # Never let a mail failure reach the response: a 500 only for real accounts would
            # reveal who is registered. Logged (with the user id, not the email) for us to see.
            logger.exception("Password reset email failed for user %s", user.pk)


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid             = serializers.CharField()
    token           = serializers.CharField()
    new_password    = serializers.CharField(write_only=True)

    def validate(self, attrs):
        try:
            user = User.objects.get(pk=force_str(urlsafe_base64_decode(attrs['uid'])))
        except (ValueError, TypeError, OverflowError, DjangoValidationError, User.DoesNotExist):
            user = None

        if (user is None or not user.is_active or user.suspended_at or user.deleted_at
                or not default_token_generator.check_token(user, attrs['token'])):
            raise serializers.ValidationError({'token': "This reset link is invalid or has expired."})

        try:
            password_validation.validate_password(attrs['new_password'], user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({'new_password': list(e.messages)})

        attrs['user'] = user
        return attrs

    def save(self):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class MessageSerializer(serializers.Serializer):
    message = serializers.CharField()