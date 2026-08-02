"""
Base settings shared by every environment. Environment-specific files
(dev.py, staging.py, production.py) import * from here and override only
what genuinely differs.
"""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="unsafe-dev-key-override-in-env")
DEBUG = False

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])

# --------------------------------------------------------------------------
# Applications
#
# LOCAL_APPS is deliberately empty at scaffolding time (Phase 0). Apps are
# added here as they're implemented, in the dependency order fixed by
# docs/modules.md: core -> institutions -> accounts -> permissions -> audit
# -> notifications_core (Layer 0), then Layer 1, Layer 2, Layer 3.
# --------------------------------------------------------------------------

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
]

LOCAL_APPS: list[str] = [
    "apps.core",
    "apps.institutions",
    "apps.accounts",
    "apps.permissions",
    "apps.audit",
    "apps.notifications_core",
    # Layer 1 — docs/checklist.md's fixed Phase 2 build order.
    "apps.classes_streams",
    "apps.students",
    "apps.staff",
    "apps.parents",
    "apps.academics",
    "apps.timetable",
    "apps.attendance",
    "apps.admissions",
    # Layer 2 — curriculum plugins, must come after academics (docs/database.md §6).
    "apps.curriculum_cbc",
    "apps.curriculum_844",
    "apps.curriculum_british",
    "apps.curriculum_tvet",
    "apps.curriculum_university",
    # Phase 4 Stage 1 — core billing/manual payments (docs/roadmap.md).
    "apps.finance",
    # Phase 5 Stage 1 — announcements, circulars, messaging (docs/roadmap.md).
    "apps.communication",
    # Phase 6 — Library, Inventory, Clinic, Documents (docs/checklist.md's
    # fixed build order).
    "apps.library",
    "apps.inventory",
    "apps.clinic",
    "apps.documents",
]

# Hostnames exempt from tenant resolution (docs/multitenancy.md §2) — e.g.
# the platform admin/system-admin host. Empty by default: production must
# opt a host in explicitly rather than defaulting to bypassing tenant scoping.
PLATFORM_HOSTS = env.list("PLATFORM_HOSTS", default=[])

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    # First, so every response — including ones short-circuited by
    # SecurityMiddleware (e.g. an SSL redirect) — carries a correlation ID.
    "apps.core.middleware.CorrelationIdMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.institutions.middleware.TenantMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --------------------------------------------------------------------------
# Database
# --------------------------------------------------------------------------

DATABASES = {
    "default": env.db("DATABASE_URL", default="postgres://educore:educore@postgres:5432/educore"),
}
DATABASES["default"]["ATOMIC_REQUESTS"] = True

# Routes dedicated_db-tier tenants to their own database alias
# (docs/multitenancy.md §5). No such tenant exists yet, so every read/write
# still resolves to `default` in practice.
DATABASE_ROUTERS = ["apps.core.db_router.TenantDBRouter"]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTH_USER_MODEL = "accounts.User"

# --------------------------------------------------------------------------
# Internationalization
# --------------------------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Nairobi"
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------
# Static & media
# --------------------------------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------------------------------
# Object storage (MinIO, S3-compatible) — configured now, consumed once
# apps.documents exists (docs/modules.md, Layer 1).
# --------------------------------------------------------------------------

STORAGES = {
    "default": {"BACKEND": "storages.backends.s3.S3Storage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
AWS_S3_ENDPOINT_URL = env("MINIO_ENDPOINT_URL", default="http://minio:9000")
AWS_ACCESS_KEY_ID = env("MINIO_ACCESS_KEY", default="educore")
AWS_SECRET_ACCESS_KEY = env("MINIO_SECRET_KEY", default="educore-dev-secret")
AWS_STORAGE_BUCKET_NAME = env("MINIO_BUCKET_NAME", default="educore")
AWS_S3_ADDRESSING_STYLE = "path"
AWS_DEFAULT_ACL = None

# --------------------------------------------------------------------------
# Cache & Celery (Redis)
# --------------------------------------------------------------------------

REDIS_URL = env("REDIS_URL", default="redis://redis:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# Phase 5 Stage 1 — first real use of Beat's periodic-task schedule; the
# celery-beat service has always been provisioned in the docker-compose
# stack (docs/deployment.md §1) but nothing had registered a task against
# it until apps.communication.tasks.publish_due_announcements.
CELERY_BEAT_SCHEDULE = {
    "publish-due-announcements": {
        "task": "apps.communication.tasks.publish_due_announcements",
        "schedule": 300.0,  # every 5 minutes
    },
}

# --------------------------------------------------------------------------
# Django REST Framework
# --------------------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPageNumberPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "5/min",
        "user": "600/min",
        # apps.finance.views.MpesaInitiateThrottle — the one action that
        # can push an M-Pesa PIN prompt to a phone number, capped hard
        # against a compromised/malicious account (Phase 4 Stage 2).
        "mpesa_initiate": "5/hour",
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # api.exception_handlers.custom_exception_handler implements the uniform
    # error contract from docs/api-design.md §4.
    "EXCEPTION_HANDLER": "api.exception_handlers.custom_exception_handler",
}

# See docs/authentication.md §1 for the HS256-over-RS256 reasoning.
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": env("JWT_SIGNING_KEY", default=SECRET_KEY),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# The refresh token is never in the response body — httpOnly/Secure/
# SameSite=Strict cookie only (docs/authentication.md §1, §4;
# docs/frontend-architecture.md §2). No `domain` is ever set when writing
# this cookie (apps/permissions/views.py) — leaving it unset scopes the
# cookie to the exact requesting hostname, never a wildcard
# `*.educore.africa`, per docs/authentication.md §4.
REFRESH_TOKEN_COOKIE_NAME = "refresh_token"
REFRESH_TOKEN_COOKIE_PATH = "/api/v1/auth/"
# True by default (production); dev.py overrides to False since local dev
# is served over plain http:// and a browser silently drops a `Secure`
# cookie set over a non-HTTPS connection.
REFRESH_TOKEN_COOKIE_SECURE = env.bool("REFRESH_TOKEN_COOKIE_SECURE", default=True)

SPECTACULAR_SETTINGS = {
    "TITLE": "EduCore API",
    "DESCRIPTION": "Kenya-first, globally-extensible Education ERP API.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # apps.library.models.BorrowerType is deliberately one shared TextChoices
    # used by both Loan.borrower_type and Reservation.borrower_type (the same
    # "Student|Staff" concept, not two independent enums) — without this,
    # drf-spectacular derives a differently-scoped component name per usage
    # site and warns about the resulting name collision on schema generation.
    "ENUM_NAME_OVERRIDES": {
        "BorrowerTypeEnum": "apps.library.models.BorrowerType.choices",
    },
}

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_CREDENTIALS = True

# --------------------------------------------------------------------------
# Notifications — pluggable per-channel backend (apps.notifications_core)
# --------------------------------------------------------------------------

# Real provider backends land in Phase 5 (docs/roadmap.md) once
# `communication` exists and is actually driving traffic — the console
# backend remains each channel's default until a deployment explicitly
# opts in via .env, same "swap without touching call sites" shape as
# MPESA_GATEWAY_BACKEND below. Push has no provider yet (deliberately
# deferred, docs/checklist.md's Phase 5 entry).
NOTIFICATION_CHANNEL_BACKENDS = {
    "sms": env(
        "SMS_CHANNEL_BACKEND", default="apps.notifications_core.backends.ConsoleChannelBackend"
    ),
    "email": env(
        "EMAIL_CHANNEL_BACKEND", default="apps.notifications_core.backends.ConsoleChannelBackend"
    ),
    "push": "apps.notifications_core.backends.ConsoleChannelBackend",
}

# --------------------------------------------------------------------------
# Africa's Talking (SMS) — Phase 5 Stage 2 (docs/roadmap.md)
# --------------------------------------------------------------------------

# "sandbox" or "production" — selects Africa's Talking's base URL.
AFRICASTALKING_ENV = env("AFRICASTALKING_ENV", default="sandbox")
# "sandbox" is Africa's Talking's own fixed sandbox username, not a secret.
AFRICASTALKING_USERNAME = env("AFRICASTALKING_USERNAME", default="sandbox")
AFRICASTALKING_API_KEY = env("AFRICASTALKING_API_KEY", default="")
# Optional — omitted from the API request entirely when blank, letting
# Africa's Talking use the account's default sender.
AFRICASTALKING_SENDER_ID = env("AFRICASTALKING_SENDER_ID", default="")

# --------------------------------------------------------------------------
# Email (SMTP/SES) — Phase 5 Stage 3 (docs/roadmap.md). Only exercised at
# all once NOTIFICATION_CHANNEL_BACKENDS["email"] is switched on above —
# in dev/test that stays on the console backend by default, so this SMTP
# config is inert (never connected to) unless a deployment opts in to both
# layers explicitly. SES is consumed via its own SMTP endpoint here, not a
# separate SDK — see DjangoEmailChannelBackend's docstring.
# --------------------------------------------------------------------------

EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-reply@educore.africa")

# --------------------------------------------------------------------------
# M-Pesa (Safaricom Daraja) — Phase 4 Stage 2 (docs/roadmap.md)
# --------------------------------------------------------------------------

# Settings-driven backend swap, same "swap the implementation without
# touching call sites" shape as NOTIFICATION_CHANNEL_BACKENDS above. Default
# is the no-network Fake backend — a real deployment opts into the live
# gateway explicitly via .env, never by accident.
MPESA_GATEWAY_BACKEND = env(
    "MPESA_GATEWAY_BACKEND", default="apps.finance.mpesa_backends.FakeMpesaGatewayBackend"
)
# "sandbox" or "production" — selects Daraja's base URL.
MPESA_ENV = env("MPESA_ENV", default="sandbox")
MPESA_CONSUMER_KEY = env("MPESA_CONSUMER_KEY", default="")
MPESA_CONSUMER_SECRET = env("MPESA_CONSUMER_SECRET", default="")
MPESA_SHORTCODE = env("MPESA_SHORTCODE", default="")
MPESA_PASSKEY = env("MPESA_PASSKEY", default="")
# Public HTTPS origin Safaricom calls back to — e.g. https://api.educore.africa
# (docs/api-design.md §11). No trailing slash.
MPESA_CALLBACK_BASE_URL = env("MPESA_CALLBACK_BASE_URL", default="")
# Comma-separated Safaricom source IPs the callback view checks against
# (docs/api-design.md §13: "the source-IP allowlist is the actual control").
# Empty in dev — same empty-in-dev-only pattern as PLATFORM_HOSTS, since
# there's no real Safaricom traffic to allowlist locally.
MPESA_CALLBACK_IP_ALLOWLIST = env.list("MPESA_CALLBACK_IP_ALLOWLIST", default=[])

# --------------------------------------------------------------------------
# Logging — structured JSON to stdout, correlation-ID-friendly
# (docs/architecture.md §6, docs/deployment.md §7).
# --------------------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "correlation_id": {"()": "apps.core.logging.CorrelationIdLogFilter"},
    },
    "formatters": {
        "json": {
            "format": '{"level": "%(levelname)s", "time": "%(asctime)s", '
            '"logger": "%(name)s", "correlation_id": "%(correlation_id)s", '
            '"message": "%(message)s"}',
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "filters": ["correlation_id"],
        },
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}
