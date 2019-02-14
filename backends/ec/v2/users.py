from rest_framework import mixins
from rest_framework import routers
from rest_framework import viewsets

from models.users import User
from .serializers.users import NameContactSerializer


class UserView(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """
    회원 이름, 연락처 변경
    """

    queryset = User.objects.all()
    serializer_class = NameContactSerializer


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'users', UserView, base_name='users')
