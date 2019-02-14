from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from .paging import BasicListFormMixin


class TagsForm(BasicListFormMixin):
    query = serializers.CharField(
        required=False,
        help_text=_(
            "검색어 <br>'"
            "(태그명)<br>"
        )
    )
