"""
# Last Expert Build Override: 2026-03-29 23:36:11
# This comment forces Vercel to perform a fresh, clean redeployment.
Django settings for Smart College Permission Management System.
"""

from pathlib import Path
import os
from django.core.exceptions import ImproperlyConfigured
import dj_database_url
import django.template.context as context_mod

# 🚨 Python 3.14 Compatibility Patch for Django 5.1/5.1.1
# Fixes "AttributeError: 'super' object has no attribute 'dicts'" in BaseContext.__copy__
import sys

# ONLY apply this patch if on Python 3.13 or 3.14+ where this alpha bug appears
if sys.version_info >= (3, 13):
    try:
        def base_context_copy_patch(self):
            duplicate = self.__class__.__new__(self.__class__)
            duplicate.__dict__.update(self.__dict__)
            duplicate.dicts = self.dicts[:]
            return duplicate

        context_mod.BaseContext.__copy__ = base_context_copy_patch
    except Exception:
        pass


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-cpms-secret')

# 🚨 PRODUCTION DEBUG SWITCH (ONLY enablement via environment variable)
# Set V_DEBUG="True" in Vercel to see full error tracebacks remotely.
V_DEBUG = os.environ.get('V_DEBUG', 'False') == 'True'
DEBUG = os.environ.get('DEBUG', 'False') == 'True' or V_DEBUG

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

# 🚨 Security Hardening for Vercel
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# Only redirect to HTTPS if not in diagnostic V_DEBUG mode
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'False') == 'True' and not V_DEBUG

# Automatically allow Vercel domains
if 'VERCEL_URL' in os.environ:
    _v_url = os.environ.get('VERCEL_URL')
    if _v_url:
        ALLOWED_HOSTS.append(_v_url)
        if '.vercel.app' in _v_url:
            ALLOWED_HOSTS.append('.vercel.app')

# Required for CSRF protection on Vercel/Render
_csrf_origins = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins.split(',') if o.strip()]

# Auto-add common deployment domains if missing
if 'https://college-gatepass.vercel.app' not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append('https://college-gatepass.vercel.app')

# Support subdomains for both Vercel and Render defaults
if 'https://*.vercel.app' not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append('https://*.vercel.app')
CSRF_TRUSTED_ORIGINS.append('https://*.onrender.com')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',  # 🚨 Added for Whitenoise in development
    'django.contrib.staticfiles',
    'permissions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # 🚨 Correct expert placement
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'permissions.middleware.RoleBasedAccessMiddleware',
]

ROOT_URLCONF = 'college_permission_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'college_permission_system.wsgi.application'

# ── Database Configuration (Vercel / Supabase) ──
DATABASE_URL = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')

if DATABASE_URL:
    # Use PostgreSQL if any database URL is found
    # NOTE: Set conn_max_age=0 for Serverless (Vercel) to avoid connection pooler failures.
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=0, # Recommended for serverless environments
            ssl_require=False # Supabase urls have ?sslmode=require
        )
    }
elif not DEBUG:
    # If in Production (DEBUG=False) but NO Database URL is found, RAISE ERROR
    raise ImproperlyConfigured(
        "DATABASE_URL or POSTGRES_URL environment variable is MISSING on Vercel!"
    )
else:
    # Locally use SQLite (Development Only)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
# Important: include the root 'static' folder so that 'collectstatic' finds our CSS
STATICFILES_DIRS = [
    BASE_DIR / 'static',
] 
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise Configuration (Senior Expert)
if not DEBUG:
    # Better WhiteNoise settings for Vercel: allow fallback to non-compressed if manifest fails
    # Standard Compressed backend (avoiding Manifest errors for stability)
    STORAGES = {
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
        },
    }
    WHITENOISE_MANIFEST_STRICT = False 
    WHITENOISE_KEEP_ONLY_HASHED_FILES = True
    WHITENOISE_USE_FINDERS = True # Help find files if manifest is missing

# ── Logging Configuration (Help debug 500s on Vercel) ──
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG' if DEBUG else 'INFO',
    },
}

# ── File Storage Paths ──
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Authentication ──
AUTH_USER_MODEL = 'permissions.CustomUser'
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

# ── Real SMTP Configuration (Gmail) ──
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
# 🚨 REPLACE THESE WITH YOUR ACTUAL DETAILS:
EMAIL_HOST_USER = 'pr.anbu969@gmail.com'
EMAIL_HOST_PASSWORD = 'hfefqqhgkmpvadlv' 
DEFAULT_FROM_EMAIL = 'Smart CPMS Admin <noreply@smartcpms.edu>'

# ── Session Security ──
SESSION_COOKIE_AGE = 3600          # 1 hour session timeout
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# 🚨 Mandatory for Production HTTPS (Vercel)
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'

# ── Login Attempt Limiting (Cache-based) ──
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Max failed login attempts before temp lockout
LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCKOUT_MINUTES = 15

# ── Password reset token validity ──
PASSWORD_RESET_TIMEOUT = 3600  # 1 hour in seconds
