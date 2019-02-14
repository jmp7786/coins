from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from backends.api.v2.responses.paging import Paging
from models.tags import Tag


class TagBasic(serializers.ModelSerializer):
    tag_id = serializers.IntegerField(
        source='id',
        help_text=_("태그 항번")
    )

    class Meta:
        model = Tag
        fields = ('tag_id', 'name', 'count')


class TagsResponse(serializers.Serializer):
    tags = TagBasic(
        many=True,
        help_text=_("태그 리스트")
    )

    total_count = serializers.IntegerField(
        required=False,
        help_text=_("태그 카운팅 (1페이지일때만 노출)")
    )

    paging = Paging(
        help_text=_("페이징 정보")
    )
