from django.conf import settings
from django.conf.urls import url, include

from . import v2

urlpatterns = [

    url(r'^ads/v2/', include(v2.urls)),

]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns.append(url(r'^__debug__/', include(debug_toolbar.urls)))
