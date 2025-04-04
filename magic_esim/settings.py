import os
from pathlib import Path
from datetime import timedelta
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

import cloudinary
import cloudinary.uploader
import cloudinary.api
import cloudinary_storage

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = [
    "magicesim.onrender.com",
    "esimmagic.com",
    "www.esimmagic.com",
    "esimmagic.flutterflow.app",
    "localhost",
    "209.74.89.107",
    "127.0.0.1",
    "localhost:8080",
    "127.0.0.1:8000",
]

SPECTACULAR_SETTINGS = {
    'TITLE': 'Magic eSIM API',
    'DESCRIPTION': 'N/A',
}

# Installed Apps
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    "drf_spectacular",
    "cloudinary",
    "cloudinary_storage",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "users",
    "esim",
    "billing",
    "frontend",
    "virtual_number",
]


SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'email',
            'profile',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}


# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    "http://209.74.89.107",
    "http://localhost",
    "http://localhost:8000",
    "https://magicesim.onrender.com",
    "https://www.esimmagic.com",
    "https://esimmagic.flutterflow.app",
    "https://esimmagic.com",
]

CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    "http://209.74.89.107",
    "http://localhost",
    "http://localhost:8000",
    "https://magicesim.onrender.com",
    "https://www.esimmagic.com",
    "https://esimmagic.flutterflow.app",
    "https://esimmagic.com",
]

# Root URL Configuration
ROOT_URLCONF = 'magic_esim.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
            BASE_DIR / 'templates' / 'partials',  # Add this line
        ],
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

# WSGI Application
WSGI_APPLICATION = 'magic_esim.wsgi.application'

# Database (PostgreSQL Configuration)
if DEBUG:
    # Development environment (local database)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST'),
            'PORT': config('DB_PORT', default=5432),
        }
    }
else:
    # Production environment (External database)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST'),
            'PORT': config('DB_PORT', default=5432),
            'OPTIONS': {
                'sslmode': 'disable',  # Enforce SSL in production
            },
        }
    }

# Password Validation
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

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static Files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles/')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default Auto Field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication
AUTH_USER_MODEL = 'users.User'  # Use custom user model
LOGIN_URL = 'frontend_login'

# REST Framework Configuration
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',  # For web (session-based)
        'rest_framework_simplejwt.authentication.JWTAuthentication',  # For API (JWT-based)
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

# Simple JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.getenv("CLOUD_NAME"),
    "API_KEY": os.getenv("CLOUD_API_KEY"),
    "API_SECRET": os.getenv("CLOUD_API_SECRET"),
}

cloudinary.config(
    cloud_name=config('CLOUDINARY_CLOUD_NAME'),
    api_key=config('CLOUDINARY_API_KEY'),
    api_secret=config('CLOUDINARY_API_SECRET'),
)

DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT')
EMAIL_USE_SSL = config('EMAIL_USE_SSL')
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')

# CoinPayments Configuration
COINPAYMENTS_MERCHANT_ID = config('COINPAYMENTS_MERCHANT_ID')
COINPAYMENTS_PUBLIC_KEY = config('COINPAYMENTS_PUBLIC_KEY')
COINPAYMENTS_PRIVATE_KEY = config('COINPAYMENTS_PRIVATE_KEY')
COINPAYMENTS_IPN_URL = config('COINPAYMENTS_IPN_URL')

# Stripe Configuration
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY')
STRIPE_PUBLIC_KEY = config('STRIPE_PUBLIC_KEY')

TAP_SECRET_KEY = config('TAP_SECRET_KEY')
TAP_REDIRECT_URL = config('TAP_REDIRECT_URL')
TAP_API_BASE_URL = config('TAP_API_BASE_URL')

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY')
