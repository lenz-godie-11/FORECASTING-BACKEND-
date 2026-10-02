import logging

from django.conf import settings
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class ErrorMiddleware:
    """Last-resort handler: converts unhandled exceptions to a JSON 500."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception:
            if settings.DEBUG:
                raise

            logger.exception("Unhandled error while processing request.")
            return JsonResponse(
                {"success": False, "error": "Internal server error."},
                status=500,
            )
