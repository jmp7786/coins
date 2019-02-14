from settings.common import *

THIRD_PARTY_APPS = (
    # djagno allauth
    'django.contrib.sites',

    'allauth',
    'allauth.account',
    'allauth.socialaccount',

    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.kakao',

    # celery
    'celery',
    'tasks',

    'cacheback',
)

# Apps specific for this project go here.
LOCAL_APPS = (
    # custom users app
    'backends.api',
    # Your stuff: custom apps go here
)
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

ROOT_URLCONF = 'backends.api.urls'

LOGIN_URL = 'rest_framework:login'
LOGOUT_URL = 'rest_framework:logout'
LOGIN_REDIRECT_URL = '/api/swagger/'

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'basic': {
            'type': 'basic'
        }
    },
    'LOGIN_URL': LOGIN_URL,
    'LOGOUT_URL': LOGOUT_URL,
    'USE_SESSION_AUTH': True,
    'DOC_EXPANSION': 'list',
    'APIS_SORTER': 'alpha',
}

LOGGING['loggers']['backends.api'] = {
    'handlers': ['console', 'cloud_watch'],
    'level': 'ERROR',
    'propagate': True,
}

LOGGING['loggers']['cacheback'] = {
    'handlers': ['console'],
    'level': 'ERROR',
    'propagate': False,
}
