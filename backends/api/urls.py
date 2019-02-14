from django.conf import settings
from django.conf.urls import url, include
from django.http import HttpResponse
from backends.common.swagger import get_swagger_view

from . import resources
from . import v2
from .resources.notices import page_not_found, server_error

schema_view = get_swagger_view(title='SERVICE API')

handler404 = page_not_found
handler500 = server_error


def elb_health_check(request):
    return HttpResponse('health')


urlpatterns = [
    url(r'^api/health/$', elb_health_check),
    url(r'^api/v2/', include(v2.urls)),

    url(r'^api/o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    url(r'^api/restframework/', include('rest_framework.urls', namespace='rest_framework')),

    url(r'^webview/', include(resources.urls)),
]

if settings.DEBUG:
    # swagger
    urlpatterns.append(url(r'^api/swagger/$', schema_view), )

    import debug_toolbar

    urlpatterns.append(url(r'^__debug__/', include(debug_toolbar.urls)))
