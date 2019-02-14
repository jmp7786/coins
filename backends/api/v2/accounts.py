from allauth.socialaccount.providers.facebook.provider import FacebookProvider
from allauth.socialaccount.providers.kakao.provider import KakaoProvider
from django.utils.translation import ugettext_lazy as _
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import F

from backends.api import exceptions
from backends.api.v2.forms.accounts import SignInForm, SignUpForm, SimpleEmailForm, ChangePasswordForm, \
    ConnectSocialAccountForm, AndroidLoginForm, SimpleNicknameForm, DisConnectSocialAccountForm
from backends.api.v2.responses.users import UserLoginResponse, AccountResponse
from libs.auth.backends import custom_auth
from libs.aws.utils import compair_push_token, edit_profile_image_by_url, temporary_password_send_email
from libs.elasticsearch.reviews import elasticsearch_reviews
from libs.oauth2.permissions import CustomIsAuthenticated
from libs.utils import get_client_ip, make_temporary_password, local_now
from models.messages import MessageBox, MessageCategory
from models.reviews import Review
from models.social import SocialAccount
from models.users import User
from services.reviews import service as review_service
from cash_db.redis_utils import period_zrem

class SignInView(APIView):
    """
    회원 로그인
    """
    permission_classes = (CustomIsAuthenticated,)

    parameter_classes = {
        'post': SignInForm,
    }

    response_docs = {
        'post': {
            '200': {
                'description': '로그인 성공',
                'schema': {
                    'type': 'object',
                    'properties': AccountResponse
                }
            },
            '400': {
                'description': '유효하지 않은 요청 파라미터',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'detail': {
                            'type': 'string'
                        },
                        'message': {
                            'type': 'string'
                        },
                        'code': {
                            'type': 'string'
                        }
                    }
                },
            },
            '404': {
                'description': '없는 이메일 혹은 등록되지 않는 SNS uid로 로그인 시도',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'detail': {
                            'type': 'string'
                        },
                        'message': {
                            'type': 'string'
                        },
                        'code': {
                            'type': 'string'
                        }
                    }
                },
            },
            '409': {
                'description': '탈퇴한 회원 이메일로 로그인 시도',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'detail': {
                            'type': 'string'
                        },
                        'message': {
                            'type': 'string'
                        },
                        'code': {
                            'type': 'string'
                        }
                    }
                },
            }
        },
    }

    def post(self, request, *args, **kwargs):
        """
        회원 로그인
        ---
        - method:      (필수) 로그인 방식 ( 'email', 'facebook', 'kakao' 중 하나) <br>
        - email:       (옵션) email (회원 아이디 *method 가 email 일 경우 필수) <br>
        - password:    (옵션) 비밀번호 (*method 가 email 일 경우 필수) <br>
        - uid:	     (필수) sns 인증 아이디 (*method 가 'facebook' or 'kakao' 일 경우 필수) <br>
        - regid:   	 (안드로이드 필수) push token 갱신용 파라미터 <br>

        <br>
        <b>헤더</b>
        - UID:        (필수) push token 갱신용 파라미터 <br>
        - TOKEN:	   (아이폰 필수) push token 갱신용 파라미터 <br>
        """
        response = dict()

        # 유효성 검사
        params = SignInForm(data=request.data)
        params.is_valid(raise_exception=True)

        method = params.validated_data.get('method')
        uid = params.validated_data.get('uid')

        uuid = request.META.get('HTTP_UID')

        os_info = request.META.get('HTTP_OS')
        token = request.META.get('HTTP_TOKEN')
        if os_info == 'aos' and not token:
            token = params.validated_data.get('regid')

        # 인증
        if method == 'facebook':
            provider = FacebookProvider(request)
            try:
                sociallogin = SocialAccount.objects.get(provider=provider.id, uid=uid)
            except SocialAccount.DoesNotExist:
                raise exceptions.NoSocialLogin

            try:
                user = User.objects.get(id=sociallogin.user_id)
            except User.DoesNotExist:
                raise exceptions.NoEmail

        elif method == 'kakao':
            provider = KakaoProvider(request)
            try:
                sociallogin = SocialAccount.objects.get(provider=provider.id, uid=uid)
            except SocialAccount.DoesNotExist:
                raise exceptions.NoSocialLogin

            try:
                user = User.objects.get(id=sociallogin.user_id)
            except User.DoesNotExist:
                raise exceptions.NoEmail

        else:
            user = custom_auth.authenticate(
                email=params.data.get('email'),
                password=params.data.get('password')
            )
            if user is None:
                raise exceptions.NoEmail
            elif not user.is_active:
                raise exceptions.IsInactiveUser

        # push 토큰 업데이트
        if token != 'NO':
            if token and uuid:
                user.uuid = uuid
                if os_info == 'aos':
                    user.regid = token
                elif os_info == 'ios':
                    user.apns = token
                user.save()

                compair_push_token(
                    platform=os_info,
                    user_id=user.id,
                    uuid=uuid,
                    token=token
                )

        user.last_login = local_now()
        user.login_count = F('login_count') +1
        user.save()

        # 프로필 정보
        response['user'] = UserLoginResponse(user).data

        return Response(response, status=status.HTTP_200_OK)


sign_in = SignInView.as_view()


class SignUpView(APIView):
    """
    회원 가입
    """
    permission_classes = (CustomIsAuthenticated,)

    parameter_classes = {
        'post': SignUpForm,
    }

    response_docs = {
        'post': {
            '200': {
                'description': '회원 가입 성공',
                'schema': {
                    'type': 'object',
                    'properties': AccountResponse
                }
            },
            '400': {
                'description': '유효하지 않은 요청 파라미터',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'detail': {
                            'type': 'string'
                        },
                        'message': {
                            'type': 'string'
                        },
                        'code': {
                            'type': 'string'
                        }
                    }
                },
            },
            '409': {
                'description': '탈퇴한 회원의 이메일로 회원가입 시도',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'detail': {
                            'type': 'string'
                        },
                        'message': {
                            'type': 'string'
                        },
                        'code': {
                            'type': 'string'
                        }
                    }
                },
            }
        },
    }

    def post(self, request):
        """
        회원 가입
        ---
        - method:      (필수) 로그인 방식 ( 'email', 'facebook', 'kakao' 중 하나) <br>
        - email:       (필수) email  <br>
        - password:    (필수) 비밀번호 <br>
        - uid:	     (옵션) sns 인증 아이디 (*method 가 'facebook' or 'kakao' 일 경우 필수) <br>
        - image_url: (옵션) sns 추가 정보 <br>
        - regid:   	 (안드로이드 필수) push token 갱신용 파라미터 <br>
        <br>
        <b>헤더</b>
        - UID:        (필수) push token 갱신용 파라미터 <br>
        - TOKEN:	   (아이폰 필수) push token 갱신용 파라미터 <br>
        """
        response = dict()

        # 유효성 검사
        form = SignUpForm(data=request.data)
        form.is_valid(raise_exception=True)

        method = form.validated_data.get('method')
        uid = form.validated_data.get('uid')
        image_url = form.validated_data.get('image_url')

        uuid = request.META.get('HTTP_UID')
        os_info = request.META.get('HTTP_OS')
        token = request.META.get('HTTP_TOKEN')

        if os_info == 'aos' and not token:
            token = form.validated_data.get('regid')

        # 새 계정 instance 생성
        user = User.objects.create_user(
            username=form.validated_data.get('email'),
            password=form.validated_data.get('password'),
            nickname=form.validated_data.get('nickname').strip(),
            date_joined=local_now(),
            ip_address=get_client_ip(request),
            uuid=uuid,
            last_login=local_now(),
        )
        token_dict = {'aos': 'regid', 'ios': 'apns'}
        if token_dict.get(os_info) and token != 'NO':
            setattr(user, token_dict.get(os_info), token)
            user.save()

        # SNS 정보가 있다면 allauth socialaccount instance 생성

        if method == 'facebook':
            provider = FacebookProvider(request)
            if not SocialAccount.objects.filter(user=user, provider=provider.id, uid=uid):
                SocialAccount(user=user, provider=provider.id, uid=uid, extra_data={}).save()

        elif method == 'kakao':
            provider = KakaoProvider(request)
            if not SocialAccount.objects.filter(user=user, provider=provider.id, uid=uid):
                SocialAccount(user=user, provider=provider.id, uid=uid, extra_data={}).save()

        # SNS extra_data 를 가지고 user field 갱신
        if image_url:
            file_info = edit_profile_image_by_url(image_url, user.id)

            if file_info:
                user.file_name_orig = file_info.get('file_org_name')
                user.file_name_save = file_info.get('file_save_name')
                user.file_dir = file_info.get('file_dir')
                user.file_size = file_info.get('file_size')
                user.file_type = file_info.get('file_type')
                user.save()

        # push 토큰 업데이트
        if token != 'NO':
            if token and uuid:
                compair_push_token(
                    platform=os_info,
                    user_id=user.id,
                    uuid=uuid,
                    token=token
                )

        # 알림함 메세지 생성
        try:
            MessageBox(
                user_id=user.id, category=MessageCategory.objects.get(name='가입완료'),
                message='반갑습니다! 글로우픽 사용이 처음이라면 꼭 확인해주세요:)'
            ).save()
        except:
            pass

        # 프로필 정보
        response['user'] = UserLoginResponse(user).data

        return Response(response, status=status.HTTP_201_CREATED)


sign_up = SignUpView.as_view()


class SimpleEmailValidationView(APIView):
    """
    이메일 가입여부 확인
    """
    permission_classes = (CustomIsAuthenticated,)

    parameter_classes = {
        'post': SimpleEmailForm,
    }

    response_docs = {
        'post': {
            '200': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'is_existed': {
                            'type': 'boolean',
                            'description': "가입된 이메일 존재 여부"
                        },
                        'is_facebook': {
                            'type': 'boolean',
                            'description': "facebook 연동 여부"
                        },
                        'is_kakao': {
                            'type': 'boolean',
                            'description': "kakao 연동 여부"
                        },
                        'is_retired': {
                            'type': 'boolean',
                            'description': "탈퇴한 회원 여부"
                        }
                    }
                }
            },
        },
    }

    def post(self, request):
        """
        이메일 가입여부 확인
        ---
        - email:       (필수) email  <br>
        """
        form = SimpleEmailForm(data=request.data)
        form.is_valid()

        response = dict()
        response['is_facebook'] = False
        response['is_kakao'] = False
        response['is_retired'] = False

        # 연동 여부 응답
        if form.errors:
            try:
                user = User.objects.get(email=form.data.get('email'))
                response['is_existed'] = True
                if not user.is_active:
                    response['is_retired'] = True
                socialaccounts = SocialAccount.objects.filter(user=user)
                for social in socialaccounts:
                    response['is_' + social.provider] = True

            except User.DoesNotExist:
                response['is_existed'] = False
        else:
            response['is_existed'] = False

        return Response(response, status=status.HTTP_200_OK)


verify_email = SimpleEmailValidationView.as_view()


class SimpleNicknameValidationView(APIView):
    """
    nickname validation check
    """
    permission_classes = (CustomIsAuthenticated,)

    parameter_classes = {
        'post': SimpleNicknameForm,
    }

    response_docs = {
        'post': {
            '200': {
                'description': '유효성 확인',
                'schema': {
                    'type': 'object',
                    'properties': {
                    }
                }
            },
            '400': {
                'description': '유효하지 않은 요청 파라미터',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'detail': {
                            'type': 'string'
                        },
                        'message': {
                            'type': 'string'
                        },
                        'code': {
                            'type': 'string'
                        }
                    }
                },
            },
        },
    }

    def post(self, request):
        """
        닉네임 유효성 체크
        ---
        - nickname:       (필수) 닉네임  <br>
        """
        form = SimpleNicknameForm(data=request.data)
        form.is_valid(raise_exception=True)

        return Response({}, status=status.HTTP_200_OK)


verify_nickname = SimpleNicknameValidationView.as_view()


class ChangePasswordView(APIView):
    """
    비밀번호 변경
    """
    permission_classes = (CustomIsAuthenticated,)

    parameter_classes = {
        'post': ChangePasswordForm,
    }

    response_docs = {
        'post': {
            '200': {
                'description': '비밀번호 변경 성공',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'message': {
                            'type': 'string'
                        },
                    }
                }
            },
            '400': {
                'description': '유효하지 않은 요청 파라미터',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'detail': {
                            'type': 'string'
                        },
                        'message': {
                            'type': 'string'
                        },
                        'code': {
                            'type': 'string'
                        }
                    }
                },
            },
            '404': {
                'description': '존재하지 않는 회원의 비밀번호 변경 시도',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'detail': {
                            'type': 'string'
                        },
                        'message': {
                            'type': 'string'
                        },
                        'code': {
                            'type': 'string'
                        }
                    }
                },
            },
            '409': {
                'description': '탈퇴한 회원의 비밀번호 변경 시도',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'detail': {
                            'type': 'string'
                        },
                        'message': {
                            'type': 'string'
                        },
                        'code': {
                            'type': 'string'
                        }
                    }
                },
            },
        },
    }

    def post(self, request):
        """
        비밀번호 변경
        ---
        - old_pw:       (필수) 이전 비밀번호  <br>
        - new_pw:       (필수) 새 비밀번호  <br>

        <br>
        <b>헤더</b>
        - IDREGISTER:        (필수) 회원 항번 <br>
        """
        form = ChangePasswordForm(data=request.data)
        form.is_valid(raise_exception=True)

        try:
            cuid = int(request.META.get('HTTP_IDREGISTER') or 0)
            user = User.objects.get(id=cuid, is_active=True)
        except User.DoesNotExist:
            raise exceptions.NoUser
        except ValueError:
            raise exceptions.InvalidParameterException

        # 기존 비밀번호 유효성 체크
        user = custom_auth.authenticate(
            email=user.email,
            password=form.validated_data.get('old_pw')
        )

        if user is None:
            raise exceptions.InvalidCurrentPassword
        elif not user.is_active:
            raise exceptions.IsInactiveUser

        # 새 비밀번호 적합성 체크
        new_pw = form.validated_data.get('new_pw')
        user.set_password(new_pw)
        user.save()

        response = {
            'message': _('비밀번호 변경 성공!')
        }

        return Response(response, status=status.HTTP_200_OK)


chanage_password = ChangePasswordView.as_view()


class IssueTemporaryPasswordView(APIView):
    """
    임시 비밀번호 발급
    """

    permission_classes = (CustomIsAuthenticated,)

    parameter_classes = {
        'post': SimpleEmailForm,
    }

    response_docs = {
        'post': {
            '200': {
                'description': '임시 비밀번호 발급',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'message': {
                            'type': 'string'
                        },
                    }
                }
            },
            '400': {
                'description': '유효하지 않은 요청 파라미터',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'detail': {
                            'type': 'string'
                        },
                        'message': {
                            'type': 'string'
                        },
                        'code': {
                            'type': 'string'
                        }
                    }
                },
            },
            '404': {
                'description': '등록되지 않은 이메일로 임시 비밀번호 발급 시도',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'detail': {
                            'type': 'string'
                        },
                        'message': {
                            'type': 'string'
                        },
                        'code': {
                            'type': 'string'
                        }
                    }
                },
            },
            '409': {
                'description': '탈퇴한 회원의 이메일로 임시 비밀번호 발급 시도',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'detail': {
                            'type': 'string'
                        },
                        'message': {
                            'type': 'string'
                        },
                        'code': {
                            'type': 'string'
                        }
                    }
                },
            },
            '424': {
                'description': '이메일 전송 과정에서 오류',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'detail': {
                            'type': 'string'
                        },
                        'message': {
                            'type': 'string'
                        },
                        'code': {
                            'type': 'string'
                        }
                    }
                },
            },
        },
    }

    def post(self, request):
        """
        임시 비밀번호 발급
        ---
        - email:       (필수) email  <br>
        """
        # 유효성 체크
        form = SimpleEmailForm(data=request.data)
        form.is_valid()

        try:
            user = User.objects.get(email=form.data.get('email'))
            if not user.is_active:
                raise exceptions.ConflictException(
                    _("탈퇴한 회원입니다.")
                )
        except User.DoesNotExist:
            raise exceptions.NoUser

        new_pw = make_temporary_password()

        user.set_password(new_pw)
        user.save()

        response = dict()
        try:
            temporary_password_send_email(new_pw, user.email)
            response['message'] = _('임시 비밀번호 메일이 전송되었습니다.')
        except:
            raise exceptions.FailedEmailSending

        return Response(response, status=status.HTTP_200_OK)


issue_temporary_password = IssueTemporaryPasswordView.as_view()


class ConnectSocialAccountView(APIView):
    """
    SNS 연동
    """
    permission_classes = (CustomIsAuthenticated,)

    parameter_classes = {
        'post': ConnectSocialAccountForm,
    }

    response_docs = {
        'post': {
            '200': {
                'description': 'SNS 연동 성공',
                'schema': {
                    'type': 'object',
                    'properties': {
                    }
                }
            },
            '400': {
                'description': '유효하지 않은 요청 파라미터',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'detail': {
                            'type': 'string'
                        },
                        'message': {
                            'type': 'string'
                        },
                        'code': {
                            'type': 'string'
                        }
                    }
                },
            },
            '404': {
                'description': '존재하지 않거나 탈퇴한 회원의 SNS 연동 시도',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'detail': {
                            'type': 'string'
                        },
                        'message': {
                            'type': 'string'
                        },
                        'code': {
                            'type': 'string'
                        }
                    }
                },
            },
            '409': {
                'description': '이미 연동되어 있는 정보로 새로 연동 시도',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'detail': {
                            'type': 'string'
                        },
                        'message': {
                            'type': 'string'
                        },
                        'code': {
                            'type': 'string'
                        }
                    }
                },
            },
        },
    }

    def post(self, request):
        """
        SNS 연동
        ---
        - method:       (필수) 로그인 방식 ('facebook', 'kakao' 중 하나)  <br>
        - uid:       (필수) sns 인증 아이디 <br>

        <br>
        <b>헤더</b>
        - IDREGISTER:        (필수) 회원 항번 <br>
        """
        form = ConnectSocialAccountForm(data=request.data)
        form.is_valid(raise_exception=True)

        try:
            cuid = int(request.META.get('HTTP_IDREGISTER') or 0)
            user = User.objects.get(id=cuid, is_active=True)
        except User.DoesNotExist:
            raise exceptions.NoUser
        except ValueError:
            raise exceptions.InvalidParameterException

        method = form.validated_data.get('method')
        uid = form.validated_data.get('uid')
        extra_data = form.validated_data.get('extra_data')

        # SocialAccount 생성

        provider = FacebookProvider(request) if method == 'facebook' else KakaoProvider(request)

        if SocialAccount.objects.filter(provider=provider.id, uid=uid).exists():
            try:
                socialaccount = SocialAccount.objects.get(provider=provider.id, uid=uid, user=user)
            except SocialAccount.DoesNotExist:
                if provider.id == 'facebook':
                    raise exceptions.ConflictFacebookAccount
                elif provider.id == 'kakao':
                    raise exceptions.ConflictKakaoAccount
                else:
                    raise exceptions.ConflictSocialAccount
            socialaccount.extra_data = extra_data
            socialaccount.save()
        else:
            SocialAccount(user=user, provider=provider.id, uid=uid, extra_data=extra_data).save()

        return Response({}, status=status.HTTP_200_OK)


connection_socialaccount = ConnectSocialAccountView.as_view()


class DisConnectSocialAccountView(APIView):
    """
    SNS 연동 해지
    """
    permission_classes = (CustomIsAuthenticated,)

    parameter_classes = {
        'post': DisConnectSocialAccountForm,
    }

    response_docs = {
        'post': {
            '200': {
                'description': 'SNS 연동 해제 성공',
                'schema': {
                    'type': 'object',
                    'properties': {
                    }
                }
            },
            '400': {
                'description': '유효하지 않은 요청 파라미터',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'detail': {
                            'type': 'string'
                        },
                        'message': {
                            'type': 'string'
                        },
                        'code': {
                            'type': 'string'
                        }
                    }
                },
            },
            '404': {
                'description': '존재하지 않거나 탈퇴한 회원의 SNS 연동 해제 시도',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'detail': {
                            'type': 'string'
                        },
                        'message': {
                            'type': 'string'
                        },
                        'code': {
                            'type': 'string'
                        }
                    }
                },
            },
        },
    }

    def post(self, request):
        """
        SNS 연동 해지
        ---
        - method:       (필수) 로그인 방식 ('facebook', 'kakao' 중 하나)  <br>

        <br>
        <b>헤더</b>
        - IDREGISTER:        (필수) 회원 항번 <br>
        """
        try:
            cuid = int(request.META.get('HTTP_IDREGISTER') or 0)
            user = User.objects.get(id=cuid, is_active=True)
        except User.DoesNotExist:
            raise exceptions.NoUser
        except ValueError:
            raise exceptions.InvalidParameterException

        form = DisConnectSocialAccountForm(data=request.data)
        form.is_valid(raise_exception=True)

        method = form.validated_data.get('method')
        # uid = form.validated_data.get('uid')

        # SocialAccount 삭제

        provider = FacebookProvider(request) if method == 'facebook' else KakaoProvider(request)

        SocialAccount.objects.filter(user=user, provider=provider.id).delete()

        return Response({}, status=status.HTTP_200_OK)


disconnection_socialaccount = DisConnectSocialAccountView.as_view()


class AccountInactiveView(APIView):
    """
    회원 탈퇴

    <br>
    <b>헤더</b>
    - IDREGISTER:        (필수) 회원 항번 <br>
    """
    permission_classes = (CustomIsAuthenticated,)

    response_docs = {
        'post': {
            '200': {
                'description': '회원 비활성화 성공',
                'schema': {
                    'type': 'object',
                    'properties': {
                    }
                }
            },
            '400': {
                'description': '유효하지 않은 요청 파라미터',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'detail': {
                            'type': 'string'
                        },
                        'message': {
                            'type': 'string'
                        },
                        'code': {
                            'type': 'string'
                        }
                    }
                },
            },
            '404': {
                'description': '존재하지 않거나 이미 탈퇴한 회원의 탈퇴 시도',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'detail': {
                            'type': 'string'
                        },
                        'message': {
                            'type': 'string'
                        },
                        'code': {
                            'type': 'string'
                        }
                    }
                },
            },
            '424': {
                'description': '외부 동기화 데이터 비전시 처리 중 오류',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'detail': {
                            'type': 'string'
                        },
                        'message': {
                            'type': 'string'
                        },
                        'code': {
                            'type': 'string'
                        }
                    }
                },
            },
        },
    }

    def post(self, request):
        try:
            cuid = int(request.META.get('HTTP_IDREGISTER') or 0)
            user = User.objects.get(id=cuid, is_active=True)
        except User.DoesNotExist:
            raise exceptions.NoUser
        except ValueError:
            raise exceptions.InvalidParameterException

        try:
            SocialAccount.objects.filter(user=user).delete()

            # 작성한 리뷰 비전시 처리
            reviews = Review.objects.filter(user=user)
            reviews.update(is_display=False, when_seceded=True)
            for review in reviews:
                review_service.delete_tags(review.id)
                body = {"doc": {'isDisplay': 0}}
                elasticsearch_reviews.update(_id=review.id, body=body)

            user.is_active = False
            user.save()

            period_zrem('all',user.id)
            period_zrem('this_week', user.id)
        except:
            raise exceptions.FailedInactiveUser

        return Response({}, status=status.HTTP_200_OK)

 
inactive_user = AccountInactiveView.as_view()


class AndoroidAutoSignInView(APIView):
    permission_classes = (CustomIsAuthenticated,)

    parameter_classes = {
        'post': AndroidLoginForm,
    }

    def post(self, request, *args, **kwargs):
        """
        회원 아이디 값으로 인증하는 약식 로그인 api (안드로이드 용)
        ---
        - regid:   	 (필수) push token 갱신용 파라미터 <br>
        <br>
        <b>헤더</b>
        - IDREGISTER:        (필수) 회원 항번 <br>
        - UID:        (필수) push token 갱신용 파라미터 <br>
        """
        response = dict()

        try:
            cuid = int(request.META.get('HTTP_IDREGISTER') or 0)
            user = User.objects.get(id=cuid, is_active=True)
        except User.DoesNotExist:
            raise exceptions.NoUser
        except ValueError:
            raise exceptions.InvalidParameterException

        uuid = request.META.get('HTTP_UID')

        # 유효성 검사
        params = AndroidLoginForm(data=request.data)
        params.is_valid(raise_exception=True)

        os_info = request.META.get('HTTP_OS')
        token = request.META.get('HTTP_TOKEN')
        if os_info == 'aos' and not token:
            token = params.validated_data.get('regid')

        if token != 'NO':
            if token and uuid:
                user.uuid = uuid
                if os_info == 'aos':
                    user.regid = token
                elif os_info == 'ios':
                    user.apns = token
                user.save()

                compair_push_token(
                    platform=os_info,
                    user_id=user.id,
                    uuid=uuid,
                    token=token
                )

        user.last_login = local_now()
        user.login_count = F('login_count') +1
        user.save()

        # 프로필 정보
        response['user'] = UserLoginResponse(user).data

        return Response(response, status=status.HTTP_200_OK)


auto_login_android = AndoroidAutoSignInView.as_view()


class PushTokenUpdateView(APIView):
    permission_classes = (CustomIsAuthenticated,)

    def post(self, request, *args, **kwargs):
        """
        푸쉬토큰 수정처리 (회원, 비회원)
        ---
        <b>헤더</b>
        - IDREGISTER:        (옵션) 회원 항번 <br>
        - UID:        (필수) push token 갱신용 파라미터 <br>
        - TOKEN:   	 (필수) push token 갱신용 파라미터, android: gcm, ios: apns <br>
        """
        try:
            cuid = int(request.META.get('HTTP_IDREGISTER') or 0)
            user = User.objects.get(id=cuid, is_active=True)
            user_id = user.id
        except User.DoesNotExist:
            user_id = -1
        except ValueError:
            raise exceptions.InvalidParameterException

        params = AndroidLoginForm(data=request.data)
        params.is_valid(raise_exception=True)

        uuid = request.META.get('HTTP_UID')
        os_info = request.META.get('HTTP_OS')
        token = request.META.get('HTTP_TOKEN')
        if os_info == 'aos' and not token:
            token = params.validated_data.get('regid')

        token_dict = {'aos': 'regid', 'ios': 'apns'}
        if token_dict.get(os_info) and user_id > 0 and token != 'NO':
            setattr(user, token_dict.get(os_info), token)
            user.save()

        if token != 'NO':
            if os_info and token:
                compair_push_token(
                    platform=os_info,
                    user_id=user_id,
                    uuid=uuid,
                    token=token
                )

        return Response({}, status=status.HTTP_200_OK)


push_token_update = PushTokenUpdateView.as_view()
