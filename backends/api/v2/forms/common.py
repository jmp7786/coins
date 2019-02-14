from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _

class CursorForm(serializers.Serializer):
    cursor = serializers.IntegerField(default=None)


class IsPushForm(serializers.Serializer):
    is_push = serializers.NullBooleanField(
        required=False,
    )

    is_user_push = serializers.NullBooleanField(
        required=False,
    )

    def validate(self, attrs):
        if attrs.get('is_push') is None and attrs.get('is_user_push') is None:
            raise serializers.ValidationError(
                "is_push or is_user_push is required."
            )

        return attrs


class AppMessageForm(serializers.Serializer):
    type = serializers.ChoiceField(
        required=False,
        choices=('x1', 'x2', 'x3'),
        default='x3'
    )
    