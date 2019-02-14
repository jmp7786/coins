from rest_framework import routers
from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response

from libs.shortcuts import get_object_or_404
from models.db_common.notices import Notice
from services.notices import service as notices_service
from .forms.notices import NoticesForm
from .responses.notices import NoticeSerializer, NoticeCategorySerializer


class NoticeView(viewsets.ViewSet):
    def list(self, request):
        """
        공지사항 리스트
        """
        params = NoticesForm(data=request.GET)
        params.is_valid(raise_exception=True)

        cursor = params.data.get('cursor')
        limit = params.data.get('limit')

        response = dict()
        board_categories = notices_service.get_categories()
        categories = NoticeCategorySerializer(board_categories, many=True)

        if cursor == 1:
            response['categories'] = categories.data
            response['total_count'] = notices_service.get_list(params, only_count=True)

        notices = notices_service.get_list(params)
        dict_category = {x['category_code']: x['category_name'] for x in categories.data}
        notices = NoticeSerializer(notices, many=True, context={'dict_category': dict_category})
        response['notices'] = notices.data

        if len(response['notices']) == limit + 1:
            next_offset = cursor + 1
            del response['notices'][-1]
        else:
            next_offset = None

        response['paging'] = dict()
        if next_offset:
            response['paging']['next'] = next_offset

        return Response(response, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """
        공지사항
        """
        notice = get_object_or_404(Notice, id=pk, is_display=True)
        board_categories = notices_service.get_categories()
        categories = NoticeCategorySerializer(board_categories, many=True)
        dict_category = {x['category_code']: x['category_name'] for x in categories.data}
        serializer = NoticeSerializer(notice, context={'dict_category': dict_category})
        response = serializer.data

        return Response(response, status=status.HTTP_200_OK)


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'notices', NoticeView, base_name='notices')
