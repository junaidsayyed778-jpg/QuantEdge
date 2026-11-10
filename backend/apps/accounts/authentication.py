from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import CSRFCheck
from rest_framework.exceptions import PermissionDenied


class CookieJWTAuthentication(JWTAuthentication):

    def authenticate(self, request):
        raw_token = request.COOKIES.get("access_token")

        # Support Authorization: Bearer as a fallback
        if raw_token is None:
            return super().authenticate(request)

        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)

        # Protect cookie-authenticated requests against CSRF
        self.enforce_csrf(request)

        return user, validated_token

    def enforce_csrf(self, request):
        check = CSRFCheck(lambda request: None)
        check.process_request(request)

        reason = check.process_view(request, None, (), {})

        if reason:
            raise PermissionDenied(f"CSRF Failed: {reason}")