import json

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from rest_framework import routers
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response

from libs.aws.utils import store_requested_product_image, store_requested_ingredient_image
from libs.oauth2.permissions import CustomIsAuthenticated
from libs.shortcuts import get_object_or_404
from libs.slack.hooks import AskHook
from libs.utils import local_now
from models.products import Product
from models.questions import Question
from models.requested_products import RequestedNewProduct, RequestedEditProduct, RequestedIngredient
from models.users import User
from .forms.questions import QeustionForm, RequestForm
from .responses.common import SuccessMessageResponse


class QuestionView(viewsets.ViewSet):
    permission_classes = (CustomIsAuthenticated,)

    parameter_classes = {
        'post_create': QeustionForm
    }

    response_docs = {
        'post_create': {
            '201': {
                'description': '문의하기',
                'schema': {
                    'type': 'object',
                    'properties': SuccessMessageResponse
                }
            },
        }
    }

    def create(self, request):
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

        return Response(
            SuccessMessageResponse(response).data,
            status=status.HTTP_201_CREATED
        )


class QuestionProductView(viewsets.ViewSet):
    permission_classes = (CustomIsAuthenticated,)

    parameter_classes = {
        'post_new': RequestForm,
        'post_edit': RequestForm,
    }

    response_docs = {
        'post_new': {
            '201': {
                'description': '제품 등록 요청',
                'schema': {
                    'type': 'object',
                    'properties': SuccessMessageResponse
                }
            },
        },
        'post_edit': {
            '201': {
                'description': '제품 수정 요청',
                'schema': {
                    'type': 'object',
                    'properties': SuccessMessageResponse
                }
            },
        },
        'post_ingredient': {
            '201': {
                'description': '제품 성분 등록 요청',
                'schema': {
                    'type': 'object',
                    'properties': SuccessMessageResponse
                }
            },
        }
    }

    @list_route(methods=['post'])
    def new(self, request):
        """
        제품추가 등록요청
        ---
        'file'  키값으로 이미지 파일 전송
        """
        params = RequestForm(data=request.data)
        params.is_valid(raise_exception=True)

        user_id = request.META.get('HTTP_IDREGISTER')
        file_obj = request.FILES.get('file')

        contents = params.validated_data.get('contents')
        now = local_now().strftime('%Y%m%d%H%M%S')

        response = dict()
        try:
            requested_product = RequestedNewProduct(
                contents=contents,
                create_date=now
            )
            requested_product.user_id = int(user_id) if user_id else 1
            requested_product.save()

            if file_obj:
                file_info = store_requested_product_image(file_obj, requested_product.id)

                if file_info:
                    requested_product.file_name_orig = file_info.get('file_org_name')
                    requested_product.file_name_save = file_info.get('file_save_name')
                    requested_product.file_dir = file_info.get('file_dir')
                    requested_product.file_size = file_info.get('file_size')
                    requested_product.file_type = file_info.get('file_type')
                    requested_product.save()

            response['is_success'] = True
            response['message'] = _("소중한 정보 감사합니다! 빠르게 등록하겠습니다:)")
        except:
            response['is_success'] = False
            response['message'] = _("요청 등록에 실패하였습니다.")

        return Response(
            SuccessMessageResponse(response).data,
            status=status.HTTP_201_CREATED
        )

    @detail_route(methods=['post'])
    def edit(self, request, pk=None):
        """
        제품 수정 요청
        """
        params = RequestForm(data=request.data)
        params.is_valid(raise_exception=True)

        user_id = int(request.META.get('HTTP_IDREGISTER') or 0)
        user = get_object_or_404(User, id=user_id)
        product = get_object_or_404(Product, id=pk)

        contents = params.validated_data.get('contents')
        now = local_now().strftime('%Y%m%d%H%M%S')

        response = dict()
        try:
            RequestedEditProduct(
                contents=contents,
                product=product,
                user=user,
                create_date=now
            ).save()

            response['is_success'] = True
            response['message'] = _("소중한 정보 감사합니다! 빠르게 수정하겠습니다:)")
        except:
            response['is_success'] = False
            response['message'] = _("요청 등록에 실패하였습니다.")

        return Response(
            SuccessMessageResponse(response).data,
            status=status.HTTP_201_CREATED
        )

    @detail_route(methods=['post'])
    def ingredient(self, request, pk=None):
        """
        성분등록요청
        ---
        'file'  키값으로 이미지 파일 전송
        <br><br> 헤더 <br>
        - IDREGISTER:        (필수) 회원 항번 <br>
        """

        user_id = request.META.get('HTTP_IDREGISTER')
        file_obj = request.FILES.get('file')

        user = get_object_or_404(User, id=user_id)
        product = get_object_or_404(Product, id=pk)

        now = local_now().strftime('%Y%m%d%H%M%S')

        response = dict()
        try:
            if file_obj:
                if RequestedIngredient.objects.filter(user=user, product=product).exists():
                    response['is_success'] = False
                    response['message'] = _("이미 성분등록 요청을 하셨습니다.")
                    return Response(
                        SuccessMessageResponse(response).data,
                        status=status.HTTP_201_CREATED
                    )

                requested_ingredient = RequestedIngredient(
                    user=user,
                    product=product,
                    create_date=now
                )
                requested_ingredient.save()

                file_info = store_requested_ingredient_image(file_obj, requested_ingredient.id)

                if file_info:
                    requested_ingredient.file_name_orig = file_info.get('file_org_name')
                    requested_ingredient.file_name_save = file_info.get('file_save_name')
                    requested_ingredient.file_dir = file_info.get('file_dir')
                    requested_ingredient.file_size = file_info.get('file_size')
                    requested_ingredient.file_type = file_info.get('file_type')
                    requested_ingredient.save()

                response['is_success'] = True
                response['message'] = _("성분요청이 정상적으로 등록되었습니다.")
            else:
                response['is_success'] = False
                response['message'] = _("성분요청시 성분이미지는 필수 입니다.")
        except:
            response['is_success'] = False
            response['message'] = _("요청 등록에 실패하였습니다.")

        return Response(
            SuccessMessageResponse(response).data,
            status=status.HTTP_201_CREATED
        )


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'ask', QuestionView, base_name='ask')
router.register(r'ask/products', QuestionProductView, base_name='ask/products')
