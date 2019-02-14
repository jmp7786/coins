from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers


class AppMessage(serializers.Serializer):
    is_message = serializers.IntegerField(
        help_text=_(
            "노출 여부"
            "<br>- 0 : 바로통과"
            "<br>- 1 : 메세지노출"
        )
    )
    android_version = serializers.CharField(
        required=False,
        help_text=_("안드로이드 버전")
    )

    ios_version = serializers.CharField(
        required=False,
        help_text=_("IOS 버전")
    )

    message_text = serializers.CharField(
        help_text=_("메세지 내용")
    )

    message_type = serializers.IntegerField(
        help_text=_(
            "메세지 유형"
            "<br>- 1 : 단순메세지노출"
            "<br>- 2 : 업데이트 유무체크"
            "<br>- 3 : 메세지 노출후 강제종료 "
        )
    )

    update_type = serializers.IntegerField(
        help_text=_(
            "업데이트 유형"
            "<br>- 1 : 강제로 스토어 이동"
            "<br>- 2 : 업데이트가 있을시 확인만 노출"
            "<br>- 3 : 업데이트 여부 선택"
        )
    )


class SplashCounting(serializers.Serializer):
    review_count = serializers.IntegerField(
        help_text=_("리뷰 카운팅")
    )
    product_count = serializers.IntegerField(
        help_text=_("제품 카운팅")
    )
    
    
    
class SplashImages(serializers.Serializer):
    bg = serializers.CharField(
        allow_null=True,
        help_text='백 그라운드 이미지 경로'
    )
    top = serializers.CharField(
        allow_null=True,
        help_text='상단 이미지 경로'
    )
    bot = serializers.CharField(
        allow_null=True,
        help_text='하단 이미지 경로'
    )
    mid = serializers.CharField(
        allow_null=True,
        help_text='중단 이미지 경로'
    )


class AppMessageResponse(serializers.Serializer):
    app_message = AppMessage(
        help_text=_("앱 메세지 정보")
    )
    splash_count = SplashCounting(
        help_text=_("스플래시 카운트 정보")
    )
    image = serializers.CharField(
        required=False,
        allow_null=True,
        help_text='이미지 경로'
    )
    image_x = serializers.CharField(
        required=False,
        allow_null=True,
        help_text='이미지 경로'
    )
    splash_images = SplashImages(
        required=False,
        help_text='이미지 경로'
    )
    
