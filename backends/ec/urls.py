from django.conf import settings
from django.conf.urls import url, include

from . import v2
from backends.common.swagger import get_swagger_view

schema_view = get_swagger_view(title='EC API')

urlpatterns = [

    url(r'^ec/v2/', include(v2.urls)),
    url(r'^ec/swagger/$', schema_view),

]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns.append(url(r'^__debug__/', include(debug_toolbar.urls)))
