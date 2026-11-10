from django.conf import settings
from django.middleware.csrf import get_token

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated

from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import RegisterSerializer, LoginSerializer

from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework.authentication import CSRFCheck

class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            return Response(
                {
                    "success": True,
                    "message": "Account created successfully.",
                    "data": {
                        "id": str(user.id),
                        "username": user.username,
                        "email": user.email,
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "success": False,
                "message": "Registration failed.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        access_token = serializer.validated_data["access"]
        refresh_token = serializer.validated_data["refresh"]

        response = Response(
            {
                "success": True,
                "message": "Login successful.",
                "data": {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                },
            },
            status=status.HTTP_200_OK,
        )

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax",
            max_age=int(api_settings.ACCESS_TOKEN_LIFETIME.total_seconds()),
        )

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax",
            max_age=int(api_settings.REFRESH_TOKEN_LIFETIME.total_seconds()),
        )

        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        return Response(
            {
                "success": True,
                "message": "User retrieved successfully.",
                "data": {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
            },
            status=status.HTTP_200_OK,
        )


class CSRFTokenView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        csrf_token = get_token(request)

        return Response(
            {
                "success": True,
                "message": "CSRF token generated.",
                "data": {
                    "csrf_token": csrf_token,
                },
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response(
                {
                    "success": False,
                    "message": "Refresh token not found.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

        except TokenError:
            response = Response(
                {
                    "success": False,
                    "message": "Invalid or expired refresh token.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

            response.delete_cookie("access_token")
            response.delete_cookie("refresh_token")

            return response

        response = Response(
            {
                "success": True,
                "message": "Logout successful.",
            },
            status=status.HTTP_200_OK,
        )

        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")

        return response


class RefreshView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        # 1. CSRF protection
        django_request = request._request

        check = CSRFCheck(lambda request: None)
        check.process_request(django_request)

        reason = check.process_view(
            django_request,
            None,
            (),
            {},
        )

        if reason:
            return Response(
                {"detail": f"CSRF Failed: {reason}"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 2. Get refresh token from cookie
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response(
                {
                    "success": False,
                    "message": "Refresh token not found.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # 3. Validate and rotate tokens
        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})

        if not serializer.is_valid():
            response = Response(
                {
                    "success": False,
                    "message": "Refresh token is invalid or expired.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

            response.delete_cookie("access_token")
            response.delete_cookie("refresh_token")

            return response

        access_token = serializer.validated_data["access"]
        new_refresh_token = serializer.validated_data.get(
            "refresh",
            refresh_token,
        )

        # 4. Set new cookies
        response = Response(
            {
                "success": True,
                "message": "Token refreshed successfully.",
            },
            status=status.HTTP_200_OK,
        )

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax",
            max_age=int(api_settings.ACCESS_TOKEN_LIFETIME.total_seconds()),
        )

        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax",
            max_age=int(api_settings.REFRESH_TOKEN_LIFETIME.total_seconds()),
        )

        return response