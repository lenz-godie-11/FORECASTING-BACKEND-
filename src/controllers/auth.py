from django.contrib.auth import authenticate

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from src.auth.roles import STAFF_ROLES


class LoginController(APIView):
    """Issues JWT access/refresh tokens for ADMIN and MANAGER accounts."""

    authentication_classes = []

    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {
                    "success": False,
                    "error": "username and password are required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=username, password=password)

        if user is None:
            return Response(
                {"success": False, "error": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        group_names = set(
            user.groups.filter(name__in=STAFF_ROLES).values_list("name", flat=True)
        )
        role = next((name for name in STAFF_ROLES if name in group_names), None)

        if role is None:
            return Response(
                {
                    "success": False,
                    "error": "Access is restricted to ADMIN and MANAGER accounts.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "success": True,
                "username": user.username,
                "role": role,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )
