from rest_framework import routers
from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response

from .responses.tags import TagsResponse
from .forms.tags import TagsForm
from libs.oauth2.permissions import CustomIsAuthenticated
from services.tags import service as tags_service


class TagView(viewsets.ViewSet):
    permission_classes = (CustomIsAuthenticated,)

    parameter_classes = {
        'get_list': TagsForm,
    }

    response_docs = {
        'get_list': {
            '200': {
                'description': '리뷰 태그 리스트',
                'schema': {
                    'type': 'object',
                    'properties': TagsResponse,
                }
            },
            '400': {
                'description': 'Invalid Parameters',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'detail': {
                            'type': 'string',
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

    def list(self, request):
        """
        태그 리스트 ( 검색 )
        """

        params = TagsForm(data=request.GET)
        params.is_valid(raise_exception=True)

        cursor = params.validated_data.get('cursor')

        response = dict()
        tags = tags_service.get_list(**params.validated_data)
        response['tags'] = tags.get('list')
        response['paging'] = dict()
        next_offset = tags.get('next_offset')
        if next_offset:
            response['paging']['next'] = next_offset

        if cursor is None:
            response['total_count'] = tags_service.get_list(only_count=True, **params.validated_data)

        return Response(TagsResponse(response).data, status=status.HTTP_200_OK)


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'tags', TagView, base_name='tags')
