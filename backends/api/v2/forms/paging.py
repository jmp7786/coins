from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers


class BasicListFormMixin(serializers.Serializer):
    cursor = serializers.IntegerField(
        default=None,
        help_text=_("다음 페이지 cursor 값")
    )

    limit = serializers.IntegerField(
        default=20,
        help_text=_("한 페이지에 노출되는 항목 수")
    )
