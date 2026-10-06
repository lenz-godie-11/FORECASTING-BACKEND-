from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from src.auth.permissions import IsStaff
from src.services.obs import ObservationConflict, create_observation, list_observations
from src.validators.obs import ObservationSerializer


class ObservationController(APIView):
    """Ingests a single daily patient observation from the hospital system."""

    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == "POST":
            return [AllowAny()]
        return [IsStaff()]

    def get(self, request):
        observations = list_observations()
        return Response(
            {
                "success": True,
                "data": observations,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = ObservationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            observation, created = create_observation(
                serializer.validated_data
            )
        except ObservationConflict as exc:
            return Response(
                {"success": False, "error": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            {
                "success": True,
                "created": created,
                "data": {
                    "id": observation.id,
                    "date": observation.date,
                    "patients": observation.patients,
                    "source": observation.source,
                    "ingested_at": observation.ingested_at,
                },
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
