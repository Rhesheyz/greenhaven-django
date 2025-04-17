from pathlib import Path
from decouple import config
import os
from django.utils.translation import gettext_lazy as _



try:
    from .unfold_settings import UNFOLD
except ImportError:
    UNFOLD = {}

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG')

# ALLOWED_HOSTS = config('ALLOWED_HOSTS').split(',')
ALLOWED_HOSTS = "127.0.0.1", "localhost"


# Application definition

INSTALLED_APPS = [
    'unfold',
    "unfold.contrib.import_export",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    'unfold.contrib.filters', 
    'unfold.contrib.simple_history',
    'django_cleanup.apps.CleanupConfig',
    'rest_framework',
    'django_extensions',
    'import_export',
    'corsheaders',
    
    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'apps.ai',
    'apps.aiSeo',
    'apps.analytics',
    'apps.api',
    'apps.destinations',
    'apps.fauna',
    'apps.flora',
    'apps.health',
    'apps.kuliner',
    'apps.core',
    'apps.hotel',
    'apps.artikel',
]

LANGUAGES = [
    ("en", "English"),
    ("id", "Indonesian"),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

LANGUAGE_CODE = "en"

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.analytics.middleware.AnalyticsMiddleware',
    'apps.analytics.middleware.ComplianceLoggingMiddleware',
    'apps.ai.middleware.AIAnalyticsMiddleware',
    'apps.ai.middleware.AIFeedbackAnalyticsMiddleware',

]

ROOT_URLCONF = 'lomba_ecotourism.urls'

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
                'apps.core.context_processors.admin_stats',
                'apps.analytics.context_processors.analytics_data',
                'apps.ai.context_processors.ai_analytics_data',
            ],
        },
    },
]

WSGI_APPLICATION = 'lomba_ecotourism.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME', default='property_db'),
        'USER': config('DB_USER', default='root'),
        # 'PASSWORD': config('DB_PASSWORD', default='yourpassword'),
        'PASSWORD': "",
        'HOST': config('DB_HOST', default='127.0.0.1'),
        'PORT': config('DB_PORT', default='3306'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR / 'static'),
]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media/'

API_BASE_URL = 'http://127.0.0.1:8000/api'  # Development

REQUEST_TIMEOUT = 5  # seconds

API_GEMINI_KEY = config('API_GEMINI_KEY')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOWED_ORIGINS = [
    "https://greenhaven.rwiconsulting.tech",
    "https://www.greenhaven.rwiconsulting.tech",
    
]

# Image kompres setting
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_IMAGE_DIMENSION = 2000  # pixels
IMAGE_QUALITY = 95  # 0-100

# For production
if not DEBUG:  # Hanya aktif di production
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_HSTS_SECONDS = 0



# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'handlers': {
#         'console': {
#             'class': 'logging.StreamHandler',
#         },
#     },
#     'loggers': {
#         'core.context_processors': {
#             'handlers': ['console'],
#             'level': 'DEBUG',
#         },
#     },
# }
