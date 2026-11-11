import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.environ.get("DJANGO_DEBUG") == "1"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or (
    "local-development-only-petcare" if DEBUG else None
)
if not SECRET_KEY:
    raise RuntimeError("Configura DJANGO_SECRET_KEY antes de iniciar PetCare.")
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "rest_framework", "clinic",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "petcare.urls"
WSGI_APPLICATION = "petcare.wsgi.application"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
# Gunicorn recibe las credenciales de PostgreSQL mediante el archivo de entorno de systemd.
DATABASES = {"default": {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": os.environ.get("POSTGRES_DB", "petcare"),
    "USER": os.environ.get("POSTGRES_USER", "petcare"),
    "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
    "HOST": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
    "PORT": os.environ.get("POSTGRES_PORT", "5432"),
}}
if DEBUG and os.environ.get("PETCARE_DEV_SQLITE") == "1":
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3",
    }
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": f"django.contrib.auth.password_validation.{name}"}
    for name in (
        "UserAttributeSimilarityValidator", "MinimumLengthValidator",
        "CommonPasswordValidator", "NumericPasswordValidator",
    )
]
LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "login"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = os.environ.get("DJANGO_HTTPS") == "1"
SECURE_SSL_REDIRECT = SESSION_COOKIE_SECURE
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}
