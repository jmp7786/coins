from rest_framework import routers
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response

from libs.oauth2.permissions import CustomIsAuthenticated
from services.recommends import service as recommend_service
from .forms.recommends import RecommendKeywordForm
from .responses.recommends import RecommendKeywordResponse


class RecommendView(viewsets.ViewSet):
    permission_classes = (CustomIsAuthenticated,)

    parameter_classes = {
        'get_keywords': RecommendKeywordForm,
    }

    response_docs = {
        'get_keywords': {
            '200': {
                'description': '추천 검색어 리스트',
                'schema': {
                    'type': 'object',
                    'properties': RecommendKeywordResponse,
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

    @list_route(methods=['get'])
    def keywords(self, request):
        """
        추천 검색어 리스트
        """
        params = RecommendKeywordForm(data=request.GET)
        params.is_valid(raise_exception=True)

        try:
            res = recommend_service.get_recommend_words_by_dynamodb(**params.validated_data)
        except:
            res = recommend_service.get_recommend_words(**params.validated_data)

        return Response(RecommendKeywordResponse(res).data, status=status.HTTP_200_OK)


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'recommends', RecommendView, base_name='recommends')
