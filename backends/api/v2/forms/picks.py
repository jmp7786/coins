from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from .paging import BasicListFormMixin


class PicksForm(serializers.Serializer):
    cursor = serializers.IntegerField(
        default=None,
        help_text=_(
            "페이징 처리 cursor"
            "<br><b>(*첫번째 리스트는 값을 넣지 않아야 함)</b>"
        )
    )

    category_id = serializers.IntegerField(
        required=False,
        help_text=_("캐스트(픽) 카테고리 항번")
    )


class UserPicksForm(PicksForm):
    pass


class PickCommentsForm(BasicListFormMixin):
    pass


class PickCommentForm(serializers.Serializer):
    comment = serializers.CharField(
        help_text=_("댓글")
    )

class PickProductsForm(BasicListFormMixin):
    pass

