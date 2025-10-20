import os
from pathlib import Path
from decouple import config

DEBUG = True
BASE_DIR = Path(__file__).resolve().parents[2]
SECRET_KEY = config('SECRET_KEY')
VIDEO_DIR = os.path.join(BASE_DIR, 'frontend', 'static', 'video')
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'capdi-y8m-640-crowdah-v1-fp32-pt-20250609.pt')

ROOT_URLCONF = "backend.config.urls"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
WSGI_APPLICATION = "backend.config.wsgi.application"
ASGI_APPLICATION = "backend.config.asgi.application"
LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake', # 아무 이름이나 지정
    }
}

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "backend.videostream",
]

ALLOWED_HOSTS = [
    '54.196.225.37', 
    '50.16.92.195',
    'cafe-empty.duckdns.org',
    'cafe-empty.duckdns.org:8000',
    'localhost', 
    '127.0.0.1'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


static_dir_path = os.path.join(BASE_DIR, 'frontend', 'static')
file_path = os.path.join(static_dir_path, 'project.css')

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    static_dir_path,
]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') 


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'frontend' / 'templates'], 
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
