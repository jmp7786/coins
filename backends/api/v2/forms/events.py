from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from backends.api.v2.forms.paging import BasicListFormMixin


class EventListForm(BasicListFormMixin):
    TERM_CHOICES = ('ongoing', 'end')
    term = serializers.ChoiceField(
        choices=TERM_CHOICES,
        help_text=_(
            "이벤트 분류 ("
            "<br>ongoing: 진행중 이벤트, "
            "<br>end: 지난 이벤트"
            "<br>)")
    )


class EventCommentListForm(BasicListFormMixin):
    pass


class EventCommentForm(serializers.Serializer):
    comment = serializers.CharField(
        help_text=_("댓글")
    )
