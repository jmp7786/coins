from settings.common import *

THIRD_PARTY_APPS = (

)

# Apps specific for this project go here.
LOCAL_APPS = (
    # custom users app
    'backends.ec',
    # Your stuff: custom apps go here
)
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

ROOT_URLCONF = 'backends.ec.urls'

LOGGING['loggers']['backends.ec'] = {
    'handlers': ['console', 'cloud_watch'],
    'level': 'ERROR',
    'propagate': True,
}
