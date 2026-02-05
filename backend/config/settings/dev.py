from .base import *

DEBUG = True

# 允许局域网访问
ALLOWED_HOSTS = ['*']
CORS_ALLOW_ALL_ORIGINS = True

# 开发环境使用 SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
