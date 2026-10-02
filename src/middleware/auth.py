class HospitalAPIKeyMiddleware:
    """
    Authentication placeholder.

    Hospital API authentication will be added when
    the external hospital system integration is implemented.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)
