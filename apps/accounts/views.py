from django.contrib.auth import login, logout
from django.middleware.csrf import get_token
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import RegisterSerializer, UserLoginSerializer, UserSerializer


class RegisterAPI(generics.GenericAPIView):
    permission_classes  = (permissions.AllowAny,)
    serializer_class    = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoginAPI(generics.GenericAPIView):
    permission_classes  = (permissions.AllowAny,)
    serializer_class    = UserLoginSerializer

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
    permission_classes  = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        logout(request)
        return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
