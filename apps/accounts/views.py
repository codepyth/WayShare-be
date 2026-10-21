from django.contrib.auth import login, logout, update_session_auth_hash
from django.middleware.csrf import get_token
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import (
    ChangePasswordSerializer, LoginResponseSerializer, MessageSerializer, RegisterSerializer,
    UserLoginSerializer, UserSerializer,
)


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