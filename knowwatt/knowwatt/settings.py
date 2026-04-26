from pathlib import Path

import os
from dotenv import load_dotenv
load_dotenv() 


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY')
if SECRET_KEY is None:
    SECRET_KEY = "thisisarandomsecretkeyforlocallytesingonly"


DEBUG = os.environ.get('DEBUG')

if DEBUG is None:
    DEBUG = True

ALLOWED_HOSTS = ["localhost","0.0.0.0","127.0.0.1"]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'channels',

    #created app
    'account',
    'funt',
    'house',
    'device',
    'energy',
    'alert',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'knowwatt.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'knowwatt.context_processors.active_house_context',
            ],
        },
    },
]

ASGI_APPLICATION = 'knowwatt.asgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases
if os.environ.get('DEBUG') == 'True':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB', 'knowwatt'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
            'HOST': os.environ.get('DB_HOST', 'db'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }

# Channel layers configuration for real-time WebSocket support
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(os.environ.get('REDIS_HOST', 'redis'), 6379)],
        },
    },
}

# WebPush settings (optional/future)
WEBPUSH_SETTINGS = {
   "VAPID_PUBLIC_KEY": os.environ.get("VAPID_PUBLIC_KEY"),
   "VAPID_PRIVATE_KEY": os.environ.get("VAPID_PRIVATE_KEY"),
   "VAPID_ADMIN_EMAIL": os.environ.get("VAPID_ADMIN_EMAIL")
}

# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    ),
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
FRONTEND_URL = 'http://localhost:8000'

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000', # allow Vue dev server
]

LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/home/'
LOGOUT_REDIRECT_URL = '/auth/login/'

# MQTT Settings
# settings.py
import os

MQTT_BROKER   = os.environ.get("MQTT_HOST")
MQTT_PORT     = int(os.environ.get("MQTT_PORT", 8883))
MQTT_USER     = os.environ.get("MQTT_USER")
MQTT_PASSWORD = os.environ.get("MQTT_PASS")
MQTT_USE_TLS  = os.environ.get("MQTT_USE_TLS", "false").lower() == "true"
