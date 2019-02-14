from rest_framework import routers
from rest_framework import viewsets
from rest_framework.response import Response

from .responses.users import UserResponse


class UserView(viewsets.ViewSet):

    def list(self, request):
        response = {'id': 666}
        return Response(UserResponse(response).data)


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'users', UserView, base_name='users')
