from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers


class SuccessMessageResponse(serializers.Serializer):
    is_success = serializers.BooleanField(
        required=False,
        help_text=_("성공 여부")
    )
    message = serializers.CharField(
        required=False,
        help_text=_("메세지")
    )


class IsPush(serializers.Serializer):
    is_push = serializers.BooleanField(required=False)
    is_user_push = serializers.BooleanField(required=False)


class IsSocialLogin(serializers.Serializer):
    is_facebook = serializers.BooleanField(required=False)
    is_kakao = serializers.BooleanField(required=False)


class SettingsResponse(serializers.Serializer):
    push = IsPush(required=False)
    sns = IsSocialLogin(required=False)
    is_success = serializers.BooleanField(required=True)
    message = serializers.CharField(required=False)


class SettingPushResponse(SuccessMessageResponse):
    push = IsPush(required=False)
