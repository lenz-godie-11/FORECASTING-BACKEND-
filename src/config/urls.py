from django.urls import include, path


urlpatterns = [
    path("api/v1/", include("src.routes.obs")),
    path("api/v1/", include("business_logic.routes.forecast")),
]
