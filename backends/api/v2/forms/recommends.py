from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers


class RecommendKeywordForm(serializers.Serializer):
    TYPE_CHOICES = ('common', 'main', 'review')

    type = serializers.ChoiceField(
        choices=TYPE_CHOICES,
        default='common',
        help_text=_(
            "추천 검색어 종류"
            "<br>(main, review, common) "
            "<br>default: common"
        )
    )

    limit = serializers.IntegerField(
        default=5,
        help_text=_("검색어 리스트 제한")
    )

