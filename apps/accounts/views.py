from django.contrib.auth import login, logout, update_session_auth_hash
from django.middleware.csrf import get_token
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import (
    ChangePasswordSerializer, LoginResponseSerializer, MessageSerializer,
    PasswordResetConfirmSerializer, PasswordResetSerializer, RegisterSerializer,
    UserLoginSerializer, UserSerializer,
)
from .throttles import PasswordResetConfirmThrottle, PasswordResetThrottle


class RegisterAPI(generics.GenericAPIView):
    permission_classes  = (AllowAny,)
    serializer_class    = RegisterSerializer

    @extend_schema(responses={201: RegisterSerializer})
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoginAPI(generics.GenericAPIView):
    permission_classes  = (AllowAny,)
    serializer_class    = UserLoginSerializer

    @extend_schema(responses={200: LoginResponseSerializer})
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return Response({
            "user": UserSerializer(user).data,
            "csrf_token": get_token(request),
        }, status=status.HTTP_200_OK)


class LogoutAPI(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(request=None, responses={200: MessageSerializer})
    def post(self, request, *args, **kwargs):
        logout(request)
        return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)


class MeAPI(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class    = UserSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.GenericAPIView):
    permission_classes  = (IsAuthenticated,)
    serializer_class    = ChangePasswordSerializer

    @extend_schema(responses={200: MessageSerializer})
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        update_session_auth_hash(request, user)
        return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)


class PasswordResetView(generics.GenericAPIView):
    permission_classes  = (AllowAny,)
    serializer_class    = PasswordResetSerializer
    throttle_classes    = (PasswordResetThrottle,)

    @extend_schema(responses={200: MessageSerializer})
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # Same answer whether or not the account exists, so this can't reveal who is registered.
        return Response(
            {'message': "If an account exists for that email, we've sent a link. It expires in 1 hour."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(generics.GenericAPIView):
    permission_classes  = (AllowAny,)
    serializer_class    = PasswordResetConfirmSerializer
    throttle_classes    = (PasswordResetConfirmThrottle,)

    @extend_schema(responses={200: MessageSerializer})
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Password reset. Log in with your new password.'}, status=status.HTTP_200_OK)