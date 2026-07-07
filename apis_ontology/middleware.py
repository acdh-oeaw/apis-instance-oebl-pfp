from rest_framework.authtoken.models import Token


class TokenAuthMiddleware:
    """
    A simple middleware that allows to use a token to access views.
    It checks if there is a `token` passed in as a request parameter
    and then uses this token to get a user from the corresponding
    rest_framework `Token` model.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if token_key := request.GET.get("token"):
            try:
                token = Token.objects.get(key=token_key)
                request.user = token.user
            except Token.DoesNotExist:
                pass
        return self.get_response(request)
