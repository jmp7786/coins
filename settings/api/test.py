from .__init__ import *

TEST_RUNNER = 'backends.api.test.runner.ManagedModelTestRunner'
DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
        },
        'pg_master': {
            'ENGINE': 'django.db.backends.sqlite3',
        }
}
