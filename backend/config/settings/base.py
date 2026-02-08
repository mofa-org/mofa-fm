"""
Django settings for MoFA FM project.
"""
import os
from pathlib import Path
from decouple import config
import dj_database_url
from celery.schedules import crontab

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Security
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'mptt',
    'drf_yasg',

    # Local apps
    'apps.users',
    'apps.podcasts',
    'apps.interactions',
    'apps.search',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default='sqlite:///db.sqlite3'),
        conn_max_age=600
    )
}

# Password validation - 无限制
AUTH_PASSWORD_VALIDATORS = []

# Internationalization
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = config('MEDIA_ROOT', default=str(BASE_DIR.parent / 'media'))

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'users.User'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# JWT Settings
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=config('JWT_ACCESS_TOKEN_LIFETIME', default=60, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=config('JWT_REFRESH_TOKEN_LIFETIME', default=7, cast=int)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# CORS
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:5173,http://127.0.0.1:5173'
).split(',')
CORS_ALLOW_CREDENTIALS = True

# CSRF
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='https://mofa.fm,http://localhost:8000,http://127.0.0.1:8000'
).split(',')

# Celery
CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULE = {
    'dispatch-rss-schedules-every-minute': {
        'task': 'apps.podcasts.tasks.dispatch_rss_schedules_task',
        'schedule': crontab(minute='*'),
    },
}

# Audio settings
AUDIO_MAX_UPLOAD_SIZE = 500 * 1024 * 1024  # 500MB
AUDIO_ALLOWED_EXTENSIONS = ['.mp3', '.wav', '.m4a', '.flac', '.ogg']
AUDIO_OUTPUT_FORMAT = 'mp3'
AUDIO_OUTPUT_BITRATE = '192k'

# MiniMax TTS defaults (override via environment if needed)
# Updated to match MoFA Flow implementation
MINIMAX_TTS = {
    'api_key': config('MINIMAX_API_KEY', default=''),
    'model': config('MINIMAX_MODEL', default='speech-2.5-hd-preview'),
    'sample_rate': config('MINIMAX_SAMPLE_RATE', default=32000, cast=int),
    'audio_bitrate': config('MINIMAX_AUDIO_BITRATE', default=128000, cast=int),
    'audio_channel': config('MINIMAX_AUDIO_CHANNEL', default=1, cast=int),
    'enable_english_normalization': config('MINIMAX_ENABLE_ENGLISH_NORMALIZATION', default=True, cast=bool),

    # Audio batching (MoFA Flow optimization to prevent shared memory issues)
    'batch_duration_ms': config('MINIMAX_BATCH_DURATION_MS', default=2000, cast=int),

    # Time-based text segmentation (MoFA Flow approach)
    # Convert max duration to character count: max_duration * chars_per_second
    # Default: 10 seconds * 4.5 chars/second = 45 characters
    'max_segment_duration': config('MINIMAX_MAX_SEGMENT_DURATION', default=10.0, cast=float),  # seconds
    'tts_chars_per_second': config('MINIMAX_TTS_CHARS_PER_SECOND', default=4.5, cast=float),  # Conservative for Chinese

    # Enhanced punctuation marks for sentence-aware splitting (MoFA Flow)
    'punctuation_marks': config('MINIMAX_PUNCTUATION_MARKS', default='。！？.!?，,、；;：:'),

    # Random silence between speaker changes
    'silence_min_ms': config('MINIMAX_SILENCE_MIN_MS', default=300, cast=int),
    'silence_max_ms': config('MINIMAX_SILENCE_MAX_MS', default=1200, cast=int),

    # Vocal logo (prepend/append around the final mixed audio)
    'enable_vocal_logo': config('MINIMAX_ENABLE_VOCAL_LOGO', default=True, cast=bool),
    'vocal_logo_start_path': config(
        'MINIMAX_VOCAL_LOGO_START_PATH',
        default=str(BASE_DIR / 'mofa-vocal-logo-start.mp3')
    ),
    'vocal_logo_end_path': config(
        'MINIMAX_VOCAL_LOGO_END_PATH',
        default=str(BASE_DIR / 'mofa-vocal-logo-end.mp3')
    ),
}

# OpenAI-compatible API for script generation (Moonshot/Kimi)
OPENAI_API_KEY = config('OPENAI_API_KEY', default='')
OPENAI_API_BASE = config('OPENAI_API_BASE', default='https://api.moonshot.cn/v1')
OPENAI_MODEL = config('OPENAI_MODEL', default='moonshot-v1-8k')
OPENAI_REQUEST_TIMEOUT = config('OPENAI_REQUEST_TIMEOUT', default=90, cast=int)
OPENAI_JUDGE_TIMEOUT = config('OPENAI_JUDGE_TIMEOUT', default=20, cast=int)

# Trending API
TRENDING_API_URL = config('TRENDING_API_URL', default='https://hot.mofa.fm')

# Tavily Search API for AI tool calling
TAVILY_API_KEY = config('TAVILY_API_KEY', default='')
