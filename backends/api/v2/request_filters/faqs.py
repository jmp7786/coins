import django_filters
from django_filters import rest_framework as filters
from models.db_common.faqs import Faq
from django.db.models import Q


class FaqFilter(filters.FilterSet):

    service_type_cd = django_filters.CharFilter(name='service_type_cd',
                                       help_text='''서비스 타입 
                                       (
                                           (SV, 글로우픽 서비스), 
                                           (EC, 글로우픽 스토어)
                                       )''',
                                       lookup_expr='exact')

    board_detail_type_cd = django_filters.CharFilter(name='board_detail_type_cd',
                                       help_text='''게시판 상세 타입
                                       (
                                        (BT02_01, 회원정보),
                                        (BT02_02, 서비스 이용),
                                        (BT02_03, 평가단/이벤트),
                                        (BT02_04, 리뷰/랭킹),
                                        (BT02_05, 기타),
                                        (BT02_11, 주문/결제),
                                        (BT02_12, 상품/배송),
                                        (BT02_13, 취소/교환/반품/환불),
                                        (BT02_15, 스토어 이용),
                                        (BT02_16, 기타),
                                       )
                                       ''',
                                       lookup_expr='exact')

    is_best = django_filters.BooleanFilter(name='is_best',
                                           help_text='Best 고정 {1:상관없음, 2:Best, 3:Best 아님}',
                                           lookup_expr='exact')

    def filter_search(self, queryset, name, value):
        return queryset.filter(Q(question__contains=value) | Q(answer__contains=value))

    search = django_filters.CharFilter(
                                       help_text='검색', method='filter_search')

    class Meta:
        model = Faq
        fields = ()
