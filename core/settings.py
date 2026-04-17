from pathlib import Path
from environs import Env

env = Env()
env.read_env()

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Security ──────────────────────────────────────────────────────────────────
SECRET_KEY    = env.str('SECRET_KEY', 'django-insecure-change-me')
DEBUG         = env.bool('DEBUG', True)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', ['localhost', '127.0.0.1', '0.0.0.0'])

# ── Apps ──────────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'daphne',                                  # must be first for channels ASGI

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # third-party
    'channels',
    'django_celery_beat',

    # local
    'common',
    'botapp',
    'user',
    'business',
    'ticket',
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

ROOT_URLCONF    = 'core.urls'
WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'

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
            ],
        },
    },
]

# ── Database ──────────────────────────────────────────────────────────────────
USE_POSTGRES = env.bool('USE_POSTGRES', False)

if USE_POSTGRES:
    DATABASES = {
        'default': {
            'ENGINE':   'django.db.backends.postgresql',
            'NAME':     env.str('DB_NAME',     'qms'),
            'USER':     env.str('DB_USER',     'qms'),
            'PASSWORD': env.str('DB_PASSWORD', 'qms_password'),
            'HOST':     env.str('DB_HOST',     'db'),
            'PORT':     env.str('DB_PORT',     '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME':   BASE_DIR / 'db.sqlite3',
        }
    }

# ── Redis ─────────────────────────────────────────────────────────────────────
REDIS_URL = env.str('REDIS_URL', '')

# ── Django Channels ───────────────────────────────────────────────────────────
if REDIS_URL:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG':  {'hosts': [REDIS_URL]},
        }
    }
else:
    # Local dev without Redis — falls back to in-memory (no cross-process pub/sub)
    CHANNEL_LAYERS = {
        'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}
    }

# ── Celery ────────────────────────────────────────────────────────────────────
CELERY_BROKER_URL          = REDIS_URL or 'memory://'
CELERY_RESULT_BACKEND      = REDIS_URL or 'cache+memory://'
CELERY_TIMEZONE            = 'Asia/Tashkent'
CELERY_TASK_SERIALIZER     = 'json'
CELERY_RESULT_SERIALIZER   = 'json'
CELERY_ACCEPT_CONTENT      = ['json']
CELERY_BEAT_SCHEDULER      = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_TASK_ALWAYS_EAGER   = not bool(REDIS_URL)   # run tasks inline if no Redis

# ── Auth ──────────────────────────────────────────────────────────────────────
AUTH_USER_MODEL      = 'user.MyUser'
LOGIN_URL            = '/auth/login/'
LOGIN_REDIRECT_URL   = '/dashboard/'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── i18n ──────────────────────────────────────────────────────────────────────
LANGUAGE_CODE = 'uz'
TIME_ZONE     = 'Asia/Tashkent'
USE_I18N      = True
USE_TZ        = True

# ── Static / Media ────────────────────────────────────────────────────────────
STATIC_URL  = env.str('STATIC_URL', '/static/')
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL   = env.str('MEDIA_URL', '/media/')
MEDIA_ROOT  = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Messages ──────────────────────────────────────────────────────────────────
from django.contrib.messages import constants as messages_constants
MESSAGE_TAGS = {
    messages_constants.DEBUG:   'info',
    messages_constants.INFO:    'info',
    messages_constants.SUCCESS: 'success',
    messages_constants.WARNING: 'warning',
    messages_constants.ERROR:   'danger',
}

# ── Telegram ──────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN   = env.str('TOKEN', '')
TELEGRAM_WEBHOOK_URL = env.str('TELEGRAM_WEBHOOK_URL', '')
