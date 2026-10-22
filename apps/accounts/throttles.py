# apps/accounts/throttles.py
from rest_framework.throttling import SimpleRateThrottle


class BodyFieldRateThrottle(SimpleRateThrottle):
    # Counts requests per value of one request-body field, not per IP: every request reaches
    # Django through the frontend's Next.js proxy, so all users share the proxy's IP.
    field = None

    def get_cache_key(self, request, view):
        value = str(request.data.get(self.field, '')).strip().lower()
        if not value:
            return None   # nothing to count; the serializer rejects the request anyway
        return self.cache_format % {'scope': self.scope, 'ident': value}


class PasswordResetThrottle(BodyFieldRateThrottle):
    scope   = 'password_reset'
    field   = 'email'


class PasswordResetConfirmThrottle(BodyFieldRateThrottle):
    scope   = 'password_reset_confirm'
    field   = 'uid'
