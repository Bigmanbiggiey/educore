from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# No real Domain rows exist for local dev — treat the dev host(s) as
# platform hosts so TenantMiddleware doesn't 404 every request
# (docs/multitenancy.md §2). "testserver" is Django's test-client default.
PLATFORM_HOSTS = ["localhost", "127.0.0.1", "testserver"]

# Local dev is plain http:// — a browser silently drops a `Secure` cookie
# set over a non-HTTPS connection, which would make the refresh cookie
# never actually get set during local testing.
REFRESH_TOKEN_COOKIE_SECURE = False

INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa: F405
INTERNAL_IPS = ["127.0.0.1"]
