from django.utils.translation import ugettext_lazy as _
from backends.common.exceptions import NotFoundException, InvalidParameterException, FailedDependencyException, \
    ConflictException


class NoUser(NotFoundException):
    message = _("탈퇴한 회원입니다.")


class NoEmail(NotFoundException):
    message = _("로그인 정보가 일치하지 않습니다. 이메일 또는 비밀번호를 다시 확인해주세요.")


class PasswordFail(NotFoundException):
    message = _("로그인 정보가 일치하지 않습니다. 이메일 또는 비밀번호를 다시 확인해주세요.")


class IsInactiveUser(ConflictException):
    message = _("현재 사용할 수 없는 이메일 계정입니다.")


class NoSocialLogin(NotFoundException):
    message = _("등록되지 않은 아이디 입니다.")


class InvalidCurrentPassword(InvalidParameterException):
    message = _("현재 비밀번호 정보가 올바르지 않습니다.")


class InvalidNewPassword(InvalidParameterException):
    message = _("비밀번호는 8자~24자 이하로 영문 대문자, 소문자, 숫자, 특수문자 중에 2개 이상 조합되어야 합니다")


class InvalidNickname(InvalidParameterException):
    message = _("2~10자의 한글, 영어, 숫자, 기본특수문자 조합만 가능합니다")


class FailedEmailSending(FailedDependencyException):
    message = _("메일발송에 실패하였습니다. cs@glowmee.com 으로 문의주세요.")


class FailedInactiveUser(FailedDependencyException):
    message = _("탈퇴처리가 실패되었습니다.")


class ConflictSocialAccount(ConflictException):
    message = _("이미 다른 계정과 연동된 SNS 계정입니다.")


class ConflictFacebookAccount(ConflictException):
    message = _("이미 다른 계정에 연동된 페이스북 계정입니다.")


class ConflictKakaoAccount(ConflictException):
    message = _("이미 다른 계정에 연동된 카카오톡 계정입니다.")
