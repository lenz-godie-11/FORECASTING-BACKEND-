from django.urls import path

from src.controllers.obs import ObservationController


urlpatterns = [
    path(
        "obs/",
        ObservationController.as_view(),
        name="observation",
    ),
]
