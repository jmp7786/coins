import configparser
import datetime
import os
from urllib.parse import quote

import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
config = configparser.ConfigParser()
config.read(BASE_DIR + '/settings/configs/common.ini')
conf = {}
for section in config.sections():

    conf[section] = {}
    for option in config.options(section):
        conf[section][option] = config.get(section, option)

# APP CONFIGURATION
# ------------------------------------------------------------------------------
DJANGO_APPS = (
    # Default Django apps:
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Useful template tags:
    # 'django.contrib.humanize',

    # Admin
    'django.contrib.admin',

    # models
    'models',

    # rest framework
    'rest_framework',
    'rest_framework.authtoken',

    'rest_framework_swagger',

    # oauth2
    'oauth2_provider',
    'corsheaders',

    # django debug
    'debug_toolbar',
    'django_extensions',

    'django_filters',

    # crontab
    'django_crontab'
)
# See: https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS

# DEBUG = bool(os.getenv('GLOWPICKAPI_DEBUG', False))
try:
    DEBUG = os.environ['GLOWPICKAPI_DEBUG'] == 'True'
except:
    DEBUG = False

# 옵션
#DEBUG_TOOLBAR_CONFIG = {
#    "SHOW_TOOLBAR_CALLBACK" : lambda request: True,
#}

ALLOWED_HOSTS = []
for host in conf['SERVERENV']['allowed_host'].split(','):
    ALLOWED_HOSTS.append(host.strip())
EC2_PRIVATE_IP = None
try:
    EC2_PRIVATE_IP = requests.get('http://169.254.169.254/latest/meta-data/local-ipv4', timeout=1).text
except requests.exceptions.RequestException:
    pass

if EC2_PRIVATE_IP:
    ALLOWED_HOSTS.append(EC2_PRIVATE_IP)

# https://docs.djangoproject.com/en/1.8/topics/http/middleware/
MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

DEFAULT_SECRET_KEY = conf.get('SERVERENV').get('secret_key')
SECRET_KEY = os.getenv('GLOWPICK_SECRET_KEY', DEFAULT_SECRET_KEY)

# mysql

CONF_DB_AURORA_MASTER = conf.get('DATABASE-AURORA-MASTER')
CONF_DB_AURORA_READ = conf.get('DATABASE-AURORA-R-ENDPOINT')

CONF_DB_PG_MASTER = conf.get('DATABASE-PG-MASTER')
CONF_DB_PG_READ = conf.get('DATABASE-PG-R-ENDPOINT')

DATABASE_ROUTERS = ['db.routers.ModelDatabaseRouter']
DATABASES = {
    'default': {
        'ENGINE': CONF_DB_AURORA_MASTER.get('engine'),
        'NAME': CONF_DB_AURORA_MASTER.get('name'),
        'USER': CONF_DB_AURORA_MASTER.get('user'),
        'PASSWORD': CONF_DB_AURORA_MASTER.get('password'),
        'HOST': CONF_DB_AURORA_MASTER.get('host'),
        'PORT': CONF_DB_AURORA_MASTER.get('port'),
        'OPTIONS': {'charset': 'utf8mb4'},
    },
    'reader_end_point': {
        'ENGINE': CONF_DB_AURORA_READ.get('engine'),
        'NAME': CONF_DB_AURORA_READ.get('name'),
        'USER': CONF_DB_AURORA_READ.get('user'),
        'PASSWORD': CONF_DB_AURORA_READ.get('password'),
        'HOST': CONF_DB_AURORA_READ.get('host'),
        'PORT': CONF_DB_AURORA_READ.get('port'),
        'OPTIONS': {'charset': 'utf8mb4'},
    },
    'pg_master': {
        'ENGINE': CONF_DB_PG_MASTER.get('engine'),
        'NAME': CONF_DB_PG_MASTER.get('name'),
        'USER': CONF_DB_PG_MASTER.get('user'),
        'PASSWORD': CONF_DB_PG_MASTER.get('password'),
        'HOST': CONF_DB_PG_MASTER.get('host'),
        'PORT': CONF_DB_PG_MASTER.get('port'),
    },
    'pg_reader_end_point': {
        'ENGINE': CONF_DB_PG_READ.get('engine'),
        'NAME': CONF_DB_PG_READ.get('name'),
        'USER': CONF_DB_PG_READ.get('user'),
        'PASSWORD': CONF_DB_PG_READ.get('password'),
        'HOST': CONF_DB_PG_READ.get('host'),
        'PORT': CONF_DB_PG_READ.get('port'),
    },
}

DJANGO_MYSQL_REWRITE_QUERIES = True

# Amazon Web Service
AWS = {
    'access_key': conf.get('AWS').get('access_key'),
    'secret_key': conf.get('AWS').get('secret_key'),
    'region': conf.get('AWS').get('region'),
}

# CDN
CDN = conf['CDN']['domain']

# ElasticSearch
ELASTIC = {
    'host': conf.get('ELASTICSEARCH').get('host')
}

ES6 = {
    'host': conf.get('ES6').get('host')
}

# ads server
ADS_URL = conf.get('ADS').get('url')
ADS_API_KEY = conf.get('ADS').get('api_key')

# General
TIME_ZONE = 'Asia/Seoul'
LANGUAGE_CODE = 'ko-kr'
# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False
USE_L10N = True
USE_TZ = True
# LOGIN_REDIRECT_URL = '/'

# Static Files
STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, "www-data")

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "frontends"),
]

TEMPLATES = [
    {
        # See: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
        'DIRS': [
            os.path.join(BASE_DIR, 'frontends')
        ],
        'OPTIONS': {
            # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-debug
            'debug': DEBUG,
            # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-loaders
            # https://docs.djangoproject.com/en/dev/ref/templates/api/#loader-types
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
            # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                # Your stuff: custom template context processors go here
            ],
        },
    },
]

# Logging
log_file = os.path.join(BASE_DIR, "glowpick-api.log")
if not DEBUG:
    log_file = "/app/logs/error_glowpick-api.log"


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(pathname)s %(lineno)d %(module)s %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
        'rq_console': {
            'format': '%(asctime)s %(message)s',
            'datefmt': '%H:%M:%S',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'cloud_watch': {
            'level': 'ERROR',
            'class': 'libs.aws.cloudwatchlogs.CloudWatchLogsHandler',
            'formatter': 'verbose'
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': log_file,
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
conf_logger = conf.get('LOGGER')
if conf_logger:
    LOGGING['loggers']['django']['handlers'].append(conf_logger.get('handler'))

# Django Rest Framework
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': int(os.getenv('DJANGO_PAGINATION_LIMIT', 20)),
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%S%z',
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.ext.rest_framework.OAuth2Authentication',
        'rest_framework.authentication.SessionAuthentication',
        # 'rest_framework.authentication.BasicAuthentication',
        # 'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'EXCEPTION_HANDLER': 'backends.common.exceptions.custom_exception_handler',
    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',)
}

# AUTH_USER_MODEL = 'models.User'

# AUTHENTICATION_BACKENDS = [
#     # "libs.auth.backends.CustomUserModelBackend",
#     "django.contrib.auth.backends.ModelBackend"
# ]

# oauth2 toolkit
OAUTH2_PROVIDER = {
    # 30 days
    'ACCESS_TOKEN_EXPIRE_SECONDS': 2592000,
    'OAUTH2_VALIDATOR_CLASS': 'libs.oauth2.validators.OAuthValidator',
}

JWT_AUTH = {
    'JWT_SECRET_KEY': SECRET_KEY,

    'JWT_ENCODE_HANDLER':
        'rest_framework_jwt.utils.jwt_encode_handler',

    'JWT_DECODE_HANDLER':
        'rest_framework_jwt.utils.jwt_decode_handler',

    'JWT_PAYLOAD_HANDLER':
        'rest_framework_jwt.utils.jwt_payload_handler',

    'JWT_PAYLOAD_GET_USER_ID_HANDLER':
        'rest_framework_jwt.utils.jwt_get_user_id_from_payload_handler',

    'JWT_RESPONSE_PAYLOAD_HANDLER':
        'rest_framework_jwt.utils.jwt_response_payload_handler',

    'JWT_EXPIRATION_DELTA': datetime.timedelta(seconds=60 * 60),

    'JWT_AUTH_HEADER_PREFIX': 'Bearer',

    'JWT_VERIFY': True,

    'JWT_VERIFY_EXPIRATION': True,

    'JWT_ALLOW_REFRESH': True,

    'JWT_REFRESH_EXPIRATION_DELTA': datetime.timedelta(days=7),
}

# django redis
REDIS_HOST = conf.get('REDIS').get('host')
REDIS_PORT = conf.get('REDIS').get('port')
MAX_CONNECTION_POOL = conf.get('REDIS').get('max_connection')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        "TIMEOUT": 600,
        "KEY_PREFIX": 'api_cache',
        "LOCATION": [
            "redis://{}:{}/0".format(REDIS_HOST, REDIS_PORT),
        ],
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {"max_connections": int(MAX_CONNECTION_POOL)}
        }
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# django-allauth
SITE_ID = 1

ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = None
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'

SOCIALACCOUNT_AUTO_SIGNUP = False
SOCIALACCOUNT_STORE_TOKENS = False

# Celery
CELERY_APP_NAME = conf['CELERY']['celery_app_name']

BROKER_TRANSPORT_OPTIONS = {
    'polling_interval': conf['CELERY']['polling_interval'],
    'visibility_timeout': int(conf['CELERY']['visibility_timeout']),
}

# Celery Broker를 AWS sqs가 아닐 경우
# common.ini의 [CELERY] 아래 broker_url를 정의해야 함
# 예:
# broker_url = amqp://guest:guest@localhost:5672/

BROKER_TRANSPORT = conf['CELERY']['broker_transport']
if BROKER_TRANSPORT == 'sqs':
    BROKER_URL = 'sqs://{0}:{1}@'.format(
        quote(AWS['access_key'], safe=''),
        quote(AWS['secret_key'], safe='')
    )
    BROKER_TRANSPORT_OPTIONS['region'] = conf['AWS']['region']

    if DEBUG:
        BROKER_TRANSPORT_OPTIONS['queue_name_prefix'] = 'test_'
    else:
        BROKER_TRANSPORT_OPTIONS['queue_name_prefix'] = 'glowpickapi_'

else:
    BROKER_URL = conf['CELERY']['broker_url']
CELERY_DEFAULT_QUEUE = conf['CELERY']['queue_name']
CELERY_DEFAULT_EXCHANGE = CELERY_DEFAULT_QUEUE
CELERY_DEFAULT_ROUTING_KEY = CELERY_DEFAULT_QUEUE
CELERY_QUEUES = {
    CELERY_DEFAULT_QUEUE: {
        'exchange': CELERY_DEFAULT_QUEUE,
        'binding_key': CELERY_DEFAULT_QUEUE,
    }
}

# CronTab Initializing
# minute hour Days Month WeekOfDay , command
CRONJOBS = [
    ('0 10 * * *', 'scripts.categories.run'),
]
