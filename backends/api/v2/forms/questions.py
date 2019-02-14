from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers


class QeustionForm(serializers.Serializer):
    TYPE_CHOICES = (
        'etc', 'bug',
        'improve', 'event', 'b2b',
    )

    TYPE_PARAMETER = {}
    for type in TYPE_CHOICES:
        TYPE_PARAMETER[type] = type.split('-')[0] + '_id'

    type = serializers.ChoiceField(
        choices=TYPE_CHOICES,
        default='etc',
        help_text=_(
            "문의"
            "<br> bug : 오류 신고"
            "<br> improve : 기능 개선 요청"
            "<br> event : 이벤트 관련 문의"
            "<br> b2b : 광고/제휴/입점 문의"
            "<br> etc : 기타 서비스 이용 관련 문의"
        )
    )

    writer = serializers.CharField(
        default=None,
        help_text=_("담당자명")
    )
    contact = serializers.CharField(
        default=None,
        help_text=_("연락처")
    )

    brand_name = serializers.CharField(
        default=None,
        help_text=_("브랜드명(업체명)")
    )
    email = serializers.CharField(
        default=None,
        help_text=_("이메일주소")
    )
    contents = serializers.CharField(
        help_text=_("문의내용")
    )

    device_model = serializers.CharField(
        default=None,
        help_text=_("단말기 모델명")
    )
    device_os = serializers.CharField(
        default=None,
        help_text=_("단말기 os 정보")
    )
    app_version = serializers.CharField(
        default=None,
        help_text=_("사용중인 앱 버전")
    )


class RequestForm(serializers.Serializer):
    contents = serializers.CharField(
        help_text=_("요청 내용")
    )
