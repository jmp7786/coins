from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from backends.api.exceptions import InvalidNewPassword, InvalidNickname, IsInactiveUser, NoEmail
from backends.common.exceptions import InvalidParameterException
from backends.common.validators import CustomUniqueValidator
from models.users import User


def validate_sign_in_method(value):
    if value not in ['email', 'facebook', 'kakao']:
        raise serializers.ValidationError("This field is not valid.")


def validate_socialaccount_provider(value):
    if value not in ['facebook', 'kakao']:
        raise serializers.ValidationError("This field is not valid.")


def validate_new_password(value):
    """
    새 비밀번호 적합성 체크
    """
    import re

    if len(value) < 8 or len(value) > 24:
        raise InvalidNewPassword

    num_match = bool(re.search('[0-9]', value))
    small_eng_match = bool(re.search('[a-z]', value))
    big_eng_match = bool(re.search('[A-Z]', value))
    sep_match = bool(re.search('[!@#$%^&*()_+\-=\[\]{};\':\"\\\\|,.<>\\/?~`]', value))

    is_not_match = (num_match and small_eng_match) \
                   or (num_match and big_eng_match) \
                   or (small_eng_match and big_eng_match) \
                   or (small_eng_match and sep_match) \
                   or (big_eng_match and sep_match)

    if not is_not_match:
        raise InvalidNewPassword


def validate_email(value):
    """
    이메일 적합성 체크 (등록 여부, 탈퇴 여부)
    """
    try:
        user = User.objects.get(email=value)
        if not user.is_active:
            raise IsInactiveUser
    except User.DoesNotExist:
        pass


def validate_nickname(value):
    """
    닉네임 적합성 체크
    """
    import re

    if len(value) < 2 or len(value) > 10:
        raise InvalidNickname

    match = bool(re.search('[^ㄱ-ㅣ가-힣a-zA-z0-9!@#$%^&*()_+\-=\[\]{};\':\"\\\\|,.<>\\/?~`]+', value))

    if match:
        raise InvalidNickname

    if User.objects.filter(nickname=value).exists():
        raise InvalidParameterException(
            _("이미 사용중인 닉네임입니다.")
        )


class NicknameUniqueValidator(CustomUniqueValidator):
    message = _('이미 사용중인 닉네임입니다.')


class EmailUniqueValidator(CustomUniqueValidator):
    message = _('해당 이메일은 이미 사용중입니다.')


class SignInForm(serializers.ModelSerializer):
    method = serializers.CharField(
        validators=[validate_sign_in_method],
        help_text=_("(필수) 로그인 방식 ( 'email', 'facebook', 'kakao' 중 하나)")
    )
    email = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_("(옵션) email (회원 아이디 *method 가 email 일 경우 필수)")
    )
    password = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_("(옵션) 비밀번호 (*method 가 email 일 경우 필수)")
    )
    uid = serializers.CharField(
        default=None,
        help_text=_("(옵션) sns 인증 아이디 (*method 가 'facebook' or 'kakao' 일 경우 필수)")
    )

    def validate_email(self, value):
        import re
        # emoji filter
        match = bool(re.search('[^ㄱ-ㅣ가-힣a-zA-z0-9!@#$%^&*()_+\-=\[\]{};\':\"\\\\|,.<>\\/?~`]+', value))

        if match:
            raise NoEmail

        try:
            user = User.objects.get(email=value)
            if not user.is_active:
                raise IsInactiveUser
        except User.DoesNotExist:
            pass

        return value

    class Meta:
        model = User
        fields = ('email', 'password', 'method', 'uid', 'regid', 'apns')
        extra_kwargs = {
            'regid': {
                'help_text': _("(안드로이드 필수) push token 갱신용 파라미터"),
            },
            'apns': {
                'help_text': _("(옵션) push token 갱신용 파라미터"),
            }
        }


class SignUpForm(serializers.ModelSerializer):
    method = serializers.CharField(
        validators=[validate_sign_in_method],
        help_text=_("(필수) 로그인 방식 ( 'email', 'facebook', 'kakao' 중 하나)")
    )
    email = serializers.EmailField(
        validators=[validate_email, EmailUniqueValidator(queryset=User.objects.filter(is_active=True))],
        help_text=_("필수) email")
    )
    password = serializers.CharField(
        validators=[validate_new_password],
        help_text=_("(필수) password")
    )
    uid = serializers.CharField(
        default=None,
        help_text=_("(옵션) sns 인증 아이디 (*method 가 'facebook' or 'kakao' 일 경우 필수)")
    )
    image_url = serializers.URLField(
        required=False,
        help_text=_("(옵션) 이미지 URL")
    )
    nickname = serializers.CharField(
        allow_blank=True,
        validators=[validate_nickname],
        help_text=_("(필수) 닉네임")
    )

    class Meta:
        model = User
        fields = ('email', 'nickname', 'password', 'method', 'uid', 'image_url', 'regid', 'apns')
        extra_kwargs = {
            'regid': {
                'help_text': _("(안드로이드 필수) push token 갱신용 파라미터"),
            },
            'apns': {
                'help_text': _("(옵션) push token 갱신용 파라미터"),
            }
        }

    def validate(self, attrs):
        method = attrs.get('method')
        if method in ['facebook', 'kakao']:
            if not attrs.get('uid'):
                raise InvalidParameterException("uid is required.")

        return super(SignUpForm, self).validate(attrs)


class SimpleEmailForm(serializers.Serializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())],
        help_text=_("(필수) email ")
    )


class SimpleNicknameForm(serializers.Serializer):
    nickname = serializers.CharField(
        allow_blank=True,
        validators=[validate_nickname],
        help_text=_("(필수) 닉네임 ")
    )


class ChangePasswordForm(serializers.Serializer):
    old_pw = serializers.CharField(
        help_text=_("(필수) 이전 비밀번호")
    )
    new_pw = serializers.CharField(
        validators=[validate_new_password],
        help_text=_("(필수) 새 비밀번호")
    )


class ConnectSocialAccountForm(serializers.Serializer):
    method = serializers.CharField(
        validators=[validate_socialaccount_provider],
        help_text=_("(필수) 로그인 방식 ('facebook', 'kakao' 중 하나)")
    )
    uid = serializers.CharField(
        help_text=_("(필수) sns 인증 아이디 ")
    )
    extra_data = serializers.JSONField(
        default={},
        help_text=_("(옵션) 기타정보 (*JSON 형태) ")
    )


class DisConnectSocialAccountForm(ConnectSocialAccountForm):
    uid = serializers.CharField(
        required=False,
        help_text=_("(옵션) sns 인증 아이디 ")
    )


class AndroidLoginForm(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('regid', 'apns')
        extra_kwargs = {
            'regid': {
                'help_text': _("(안드로이드 필수) push token 갱신용 파라미터"),
            },
            'apns': {
                'help_text': _("(옵션) push token 갱신용 파라미터"),
            }
        }
