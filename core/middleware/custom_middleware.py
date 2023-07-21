from django.utils.deprecation import MiddlewareMixin


class CookieMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if request.path.startswith("/login"):
            response.set_cookie(
                "cookie_name", "cookie_value", samesite="None", secure=True
            )
        return response
