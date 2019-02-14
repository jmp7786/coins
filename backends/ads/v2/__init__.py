from django.conf.urls import url, include

from .users import router as user

urls = [
    url(r'', include(user.urls)),
]


