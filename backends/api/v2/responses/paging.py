from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers


class Paging(serializers.Serializer):
    next = serializers.CharField(
        required=False,
        help_text=_("다음 페이지 커서 값")
    )
