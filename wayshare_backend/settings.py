"""
Django settings for the WayShare backend.

Every secret and per-environment value is read from environment variables (or a local `.env`,
which is gitignored). `.env.example` lists them all. Nothing secret belongs in this file.
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, []),
    CORS_ALLOWED_ORIGINS=(list, []),
    CSRF_TRUSTED_ORIGINS=(list, []),
)
environ.Env.read_env(BASE_DIR / ".env")


# Core — no defaults for secrets: a missing key should fail loudly, not run insecurely.
SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

# Swagger UI at /api/docs/ — on whenever DEBUG is on, unless API_DOCS_ENABLED says otherwise.
API_DOCS_ENABLED = env.bool("API_DOCS_ENABLED", default=DEBUG)


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    "rest_framework",
    "drf_spectacular",
    "corsheaders",

    # Apps
    "apps.core",
    "apps.accounts",
    "apps.rides",
]


AUTH_USER_MODEL = "accounts.User"


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'wayshare_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'wayshare_backend.wsgi.application'


# Database — SQLite. DATABASE_URL can point it elsewhere: Docker keeps the file in a volume
# (see compose.yaml) so data survives container restarts.

DATABASES = {"default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")}


# Passwords — Argon2 first. PBKDF2 stays in the list only so existing hashes still verify;
# Django rehashes them to Argon2 on the next successful login.

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# API — session auth, deny by default. An endpoint that should be public opts out explicitly.

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Used only by views that set throttle_classes (see apps/accounts/throttles.py).
    "DEFAULT_THROTTLE_RATES": {
        "password_reset":           "5/hour",
        "password_reset_confirm":   "10/hour",
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "WayShare API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}


# Internationalization

LANGUAGE_CODE = 'en-gb'

TIME_ZONE = 'Europe/London'

USE_I18N = True

USE_TZ = True


# Static files (admin and Swagger CSS/JS) — served by runserver while DEBUG is on.

STATIC_URL = 'static/'

# Uploaded files (profile photos), on local disk. A real server would need object storage (Q10).
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email — Gmail SMTP when EMAIL_USER / EMAIL_PASSWORD are set (EMAIL_PASSWORD is a Google App
# Password, not the account password); otherwise emails are printed to the console.
EMAIL_HOST          = "smtp.gmail.com"
EMAIL_PORT          = 587
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = env("EMAIL_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_PASSWORD", default="")
EMAIL_TIMEOUT       = 10
EMAIL_BACKEND       = (
    "django.core.mail.backends.smtp.EmailBackend" if EMAIL_HOST_USER
    else "django.core.mail.backends.console.EmailBackend"
)
# Gmail sends as the logged-in account whatever From says, so From uses that address.
DEFAULT_FROM_EMAIL  = f"WayShare <{EMAIL_HOST_USER}>" if EMAIL_HOST_USER else "WayShare <no-reply@localhost>"


# Frontend — the Next.js app proxies /api/* to this server, so the browser only ever talks to the
# frontend's own origin. Django still sees that origin in the Origin header on writes, so it must be
# trusted for CSRF. CORS is only needed if a browser ever calls this server directly.

CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")
CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_CREDENTIALS = True


# Sessions — 14 days, renewed on every request: active users stay logged in, inactive ones expire.

SESSION_COOKIE_AGE = 60 * 60 * 24 * 14
SESSION_SAVE_EVERY_REQUEST = True

# Password reset links expire after 1 hour (Django's default is 3 days) and point to the frontend.
PASSWORD_RESET_TIMEOUT = 3600
FRONTEND_URL = (env("FRONTEND_URL", default="") or "http://localhost:3000").rstrip("/")

