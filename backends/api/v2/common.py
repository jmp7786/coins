import json
import logging
from os import path
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from rest_framework import routers
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework.views import APIView

from backends.api import exceptions
from backends.common.exceptions import InvalidParameterException
from libs.aws.dynamodb import aws_dynamodb_device_token
from libs.aws.dynamodb import aws_dynamodb_etc_items
from libs.aws.s3 import aws_s3_helper
from libs.aws.utils import update_is_push, update_is_user_push
from libs.oauth2.permissions import CustomIsAuthenticated
from libs.shortcuts import get_object_or_404
from libs.slack.hooks import AskHook
from libs import utils
from models.app_message import AppMessage
from models.common_codes import CommonCodeValue
from models.db_common.users_ec import EcUser
from models.events import Event
from models.picks import Pick
from models.placeholders import Placeholder
from models.products import Product
from models.questions import Question
from models.reviews import Review
from models.social import SocialAccount
from models.users import User
from .forms.common import IsPushForm, AppMessageForm
from .forms.questions import QeustionForm
from .responses.app_message import AppMessageResponse
from .responses.common import SuccessMessageResponse, SettingsResponse, SettingPushResponse


logger = logging.getLogger(__name__)

class AppMessageView(APIView):
    # permission_classes = (CustomIsAuthenticated,)
    authentication_classes = ()

    response_docs = {
        'get': {
            '200': {
                'description': 'App Message',
                'schema': {
                    'type': 'object',
                    'properties': AppMessageResponse
                }
            },
        }
    }

    def get(self, request, os):
        """
        앱 메세지
        ---
        앱 실행시 업데이트여부 및 점검 강제종류 등을 위한 앱 메세지, 스플래시 제품/리뷰 카운팅
        <br>
        <br> <b>IOS : /app_message/ios/</b>
        <br> <b>Android : /app_message/aos/</b>
        """

        if os not in ['aos', 'ios']:
            raise InvalidParameterException()

        params = AppMessageForm(data=request.GET)
        params.is_valid(raise_exception=True)
        
        
        response = dict()
        try:
            response['app_message'] = aws_dynamodb_etc_items.get_app_message(os)
            response['splash_count'] = aws_dynamodb_etc_items.get_splash_count()
        except:
            message = AppMessage.objects.get_message(os)
            if message:
                setattr(message, 'is_message', 1)
            else:
                setattr(message, 'is_message', 0)
            response['app_message'] = message
            response['splash_count'] = {
                'product_count': Product.objects.filter(is_display=True).count(),
                'review_count': Review.objects.filter(
                    is_display=True,
                    # state='N',
                    # user__is_blinded=0,
                    # product__is_display=True
                ).count()
            }
            
        # s3 에서 파일 리스트를 가져온다.
        key_path = path.join('splash',os)
        
        if os == 'aos':
            aos_type = params.validated_data.get('type')
            response['splash_images'] = dict()
            
            splash_images = {
                'bg':aws_s3_helper
                    .s3_get_dir_objects(path.join(
                        key_path,'bg',aos_type)),
                'top':aws_s3_helper
                    .s3_get_dir_objects(path.join(
                    key_path,'top',aos_type)),
                'bot':aws_s3_helper
                    .s3_get_dir_objects(path.join(
                    key_path,'bot',aos_type)),
                'mid':aws_s3_helper
                    .s3_get_dir_objects(path.join(
                    key_path,'mid',aos_type))
            }
            
            for k, v in splash_images.items():
                if len(v) > 0 :
                    # 가장 마지막에 업데이트한 파일을 반환하기 위해 마지막 변경일을 기준으로 정렬한다.
                    v.sort(key=lambda x: x.last_modified)
        
                    response['splash_images'][k] = utils.escape_last_path_in_url(
                        "{}/{}".format(settings.CDN, v[-1].key))
                else:
                    response['splash_images'][k] = None

        elif os == 'ios':
            images_m = aws_s3_helper.s3_get_dir_objects(path.join(key_path,"m"))
            
            if len(images_m) > 0 :
                images_m.sort(key=lambda x: x.last_modified)

                response['image'] = utils.escape_last_path_in_url(
                    "{}/{}".format(settings.CDN, str(images_m[-1].key)))
                
                # ios 일 경우 image_x 라는 이미지를 추가한다.
                images_x = aws_s3_helper\
                    .s3_get_dir_objects(path.join(key_path , "x"))
                
                if len(images_x) > 0 :
                    images_x.sort(key=lambda x: x.last_modified)
                    response['image_x'] = utils.escape_last_path_in_url(
                    "{}/{}".format(settings.CDN,images_x[-1].key))
                    
                else:
                    response['image_x'] = None
                    
            else:
                response['image'] = None
                response['image_x'] = None
        
        return Response(AppMessageResponse(response).data, status=status.HTTP_200_OK)


app_message = AppMessageView.as_view()


class InitailizationView(APIView):
    permission_classes = (CustomIsAuthenticated,)

    def get(self, request):
        """
        설정 값 초기화
        ---
        <br> review placeholder,
        <br> report_types
        <br> index_bottom
        """

        response = dict()

        ph = Placeholder.objects.get_review_placeholder()
        if ph:
            response['placeholder'] = ph.placeholder

        report_types = CommonCodeValue.objects.get_report_types()
        if report_types:
            response['report_types'] = report_types

        try:
            response['index_bottom'] = aws_dynamodb_etc_items.get_index_bottom()
        except:
            response['index_bottom'] = dict()
            # Pick from DB
            pick_count = Pick.objects.latest_picks().count()
            response['index_bottom']['pick_count'] = pick_count
            response['index_bottom']['pick_last_id'] = Pick.objects.displayed().latest('id').id if pick_count != 0 else 0
            # Event from DB
            event_count = Event.objects.ongoing().count()
            response['index_bottom']['event_count'] = event_count
            response['index_bottom']['event_last_id'] = Event.objects.displayed().latest('id').id if event_count != 0 else 0

        return Response(response, status=status.HTTP_200_OK)


initialize = InitailizationView.as_view()


class QuestionView(APIView):
    permission_classes = (CustomIsAuthenticated,)

    parameter_classes = {
        'post': QeustionForm
    }

    response_docs = {
        'post': {
            '201': {
                'description': 'App Message',
                'schema': {
                    'type': 'object',
                    'properties': SuccessMessageResponse
                }
            },
        }
    }

    def post(self, request):
        """
        문의하기
        """
        params = QeustionForm(data=request.data)
        params.is_valid(raise_exception=True)

        user_id = int(request.META.get('HTTP_IDREGISTER') or 0)

        _type = params.validated_data.get('type')
        contents = params.validated_data.get('contents')
        contact = params.validated_data.get('contact')
        writer = params.validated_data.get('writer')
        email = params.validated_data.get('email')
        brand_name = params.validated_data.get('brand_name')

        device_model = params.validated_data.get('device_model')
        device_os = params.validated_data.get('device_os')
        app_version = params.validated_data.get('app_version')

        extra_info = dict()
        if device_model:
            extra_info['device_model'] = device_model
        if device_os:
            extra_info['device_os'] = device_os
        if app_version:
            extra_info['app_version'] = app_version

        extra_info_json = json.dumps(extra_info)

        response = dict()
        try:
            question = Question(
                type=_type,
                contents=contents,
                user_id=user_id,
                writer_name=writer,
                brand_name=brand_name,
                contact=contact,
                email=email,
                extra_info=extra_info_json
            ).save()

            response['is_success'] = True
            response['message'] = _("문의 완료!\n빠른 답변 드리겠습니다.")

            # slack-bot message send
            if not settings.DEBUG:
                try:
                    nickname = User.objects.get(id=user_id).nickname
                except:
                    nickname = ""

                title = "요청자 : " + nickname
                desc = "문의내용 : " + contents

                slack_django = AskHook()
                slack_django.send_message(
                    title=title,
                    desc=desc,
                    question_id=question.id,
                    _type=_type
                )
        except:
            response['is_success'] = False
            response['message'] = _("등록에 실패하였습니다.")

        return Response(SuccessMessageResponse(response).data, status=status.HTTP_201_CREATED)


ask = QuestionView.as_view()


class SetPushView(viewsets.ViewSet):
    permission_classes = (CustomIsAuthenticated,)

    parameter_classes = {
        'put_push': IsPushForm,
    }

    response_docs = {
        'put_push': {
            '200': {
                'description': '일반 푸시 수신 여부 수정',
                'schema': {
                    'type': 'object',
                    'properties': SettingPushResponse,
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

    def list(self, request):
        """
        서비스 설정 정보
        ---
        <b>헤더</b>
        - IDREGISTER:        (필수) 회원 항번 <br>
        - UUID:        (필수) push token 갱신용 파라미터 <br>
        """
        user_id = request.META.get('HTTP_IDREGISTER')
        uuid = request.META.get('HTTP_UID')

        response = dict()
        response['is_success'] = True

        # push 여부 조회
        if uuid:
            item = aws_dynamodb_device_token.get_device_token(uuid)
            if item:
                is_push = item.get('isPush')
                is_user_push = item.get('isUserPush')
                if is_push or is_user_push:
                    response['push'] = dict()
                if is_push:
                    response['push']['is_push'] = True if int(is_push.get('N')) == 1 else False

                if is_user_push:
                    response['push']['is_user_push'] = True if int(is_user_push.get('N')) == 1 else False

        if response.get('push') is None:
            response['is_success'] = False
            response['message'] = _("푸시알림 설정에 필요한 정보를 받아오지 못했습니다.")

        # sns 연동 여부 조회
        if user_id and user_id != '0':
            response['sns'] = dict()
            response['sns']['is_facebook'] = False
            response['sns']['is_kakao'] = False
            try:
                user = User.objects.get(id=user_id, is_active=True)
                socialaccounts = SocialAccount.objects.filter(user=user)
                for social in socialaccounts:
                    response['sns']['is_' + social.provider] = True

            except User.DoesNotExist:
                raise exceptions.NoUser
            except ValueError:
                raise exceptions.InvalidParameterException

        return Response(data=SettingsResponse(response).data, status=status.HTTP_200_OK)

    @list_route(methods=['put'])
    def push(self, request):
        """
        push 수신 여부 수정
        """
        # user_id = request.META.get('HTTP_IDREGISTER')
        uuid = request.META.get('HTTP_UID')

        params = IsPushForm(data=request.data)
        params.is_valid(raise_exception=True)

        is_push = params.validated_data.get('is_push')
        is_user_push = params.validated_data.get('is_user_push')
        response = dict()
        response['push'] = dict()

        response['is_success'] = False
        response['message'] = _("등록에 실패하였습니다.")

        if is_push is not None and uuid:
            results = update_is_push(uuid, is_push)
            if results:
                response['push']['is_push'] = results.get('is_push')

                if results.get('status'):
                    response['is_success'] = True
                    response['message'] = _("변경에 성공하였습니다.")
                else:
                    response['is_success'] = False
                    response['message'] = _("등록에 실패하였습니다.")

            else:
                response['is_success'] = False
                response['message'] = _("푸시알림 설정에 필요한 정보를 받아오지 못했습니다.")

        if is_user_push is not None and uuid:
            results = update_is_user_push(uuid, is_user_push)
            if results:
                response['push']['is_user_push'] = results.get('is_user_push')

                if results.get('status'):
                    response['is_success'] = True
                    response['message'] = _("변경에 성공하였습니다.")
                else:
                    response['is_success'] = False
                    response['message'] = _("등록에 실패하였습니다.")
            else:
                response['is_success'] = False
                response['message'] = _("푸시알림 설정에 필요한 정보를 받아오지 못했습니다.")

        return Response(SettingsResponse(response).data, status=status.HTTP_200_OK)


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'settings', SetPushView, base_name='setup_push')


class UserModelSynchronizationView(APIView):
    permission_classes = ()

    def post(self, request):
        """
        service - ec 간 유저 모델 동기화 처리
        """
        user_id = request.POST.get('user_id')
        user = get_object_or_404(User, id=user_id)
        try:
            obj, created = EcUser.objects.get_or_create(id=user.id)
            for field in user._meta.fields:
                setattr(obj, field.name, getattr(user, field.name))
            obj.save()
        except Exception as err:
            logger.error(str(err))
        return Response(status=status.HTTP_204_NO_CONTENT)


user_model_synchronization = UserModelSynchronizationView.as_view()
