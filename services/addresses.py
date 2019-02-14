from django.db.models import Case, CharField
from django.db.models import F
from django.db.models import Q
from django.db.models import Value
from django.db.models import When
from django.db.models.functions import Concat

from models.addresses import Yoyakinfo


class AddressService:
    SIDO_NAMES = {'충북': '충청북도', '충남': '충청남도', '경북': '경상북도', '경남': '경상남도', '전북': '전라북도', '전남': '전라남도'}

    def _set_filter(self, word):
        condition = Q()
        if word.isdigit():
            condition |= Q(gichoguyeok_num=word)
            num = int(word)
            condition |= Q(building_bonbeon=num)
            condition |= Q(building_bubeon=num)
            condition |= Q(jibeonbonbeon_beonji=num)
            condition |= Q(jibeonbubeon_ho=num)
        else:
            if word in self.SIDO_NAMES.keys():
                condition |= Q(sido_name__startswith=self.SIDO_NAMES[word])
            else:
                condition |= Q(sido_name__startswith=word)
            condition |= Q(sigungu_name__startswith=word)
            condition |= Q(doromyeong__startswith=word)
            condition |= Q(beopjeongeupmyendong_name__startswith=word)
            condition |= Q(sigunguyong_building_name__startswith=word)

        return condition

    def get_list(self, params, only_count=None):
        """
        우편번호 검색
        :param params: query, cursor, limit
        :return: addresses, total_count, next_offset
        """
        query = params.data.get('query')
        limit = int(params.data.get('limit', 100) or 100)
        cursor = params.data.get('cursor', 1)
        cursor = int(cursor or 1)
        offset = (cursor - 1) * limit

        # query parameter parsing
        """
        • 도로명 + 건물번호 (예 : 테헤란로 501)
        • 동/읍/면/리 + 번지 (예: 삼성동 157-27)
        • 건물명, 아파트명 (예: 반포자이아파트)
        """
        words = query.split() if query else []
        if len(words) > 0:
            conditions = Q()
            for word in words:
                if '-' in word:
                    ns = word.split('-')
                    for no in ns:
                        conditions &= self._set_filter(no)
                else:
                    conditions &= self._set_filter(word)
        else:
            return [], 0, None

        # make query
        query_set = Yoyakinfo.objects.all()
        query_set = query_set.annotate(
            zip=F('gichoguyeok_num'),  # 새우편번호

            doromyeong_addr=Concat('sido_name', Value(' '), 'sigungu_name',
                                   Case(When(eupmyendong_gubun='0', then=F('beopjeongeupmyendong_name')),
                                        default=Value('')),
                                   Value(' '),
                                   'doromyeong',
                                   Value(' '),
                                   Case(When(is_basement='0', then=Value('')),
                                        When(is_basement='1', then=Value('지하')),
                                        When(is_basement='2', then=Value('공중')), default=Value('')),
                                   'building_bonbeon',
                                   Case(When(building_bubeon=0, then=None),
                                        default=Concat(Value('-'), F('building_bubeon'), output_field=CharField())),
                                   output_field=CharField()),  # 도로명 주소

            etc=Case(When(eupmyendong_gubun='0', is_apartment_house='0',
                          then=Value('')),
                     When(eupmyendong_gubun='0', is_apartment_house='1',
                          then=Concat(Value('('), F('sigunguyong_building_name'), Value(')'))),
                     When(eupmyendong_gubun='1', is_apartment_house='0',
                          then=Concat(Value('('), F('beopjeongeupmyendong_name'), Value(')'))),
                     When(eupmyendong_gubun='1', is_apartment_house='1',
                          then=Concat(Value('('), F('beopjeongeupmyendong_name'), Value(', '),
                                      F('sigunguyong_building_name'), Value(')')))),  # etc(동네명, 건물명)

            jibun_addr=Concat('sido_name', Value(' '), 'sigungu_name', Value(' '),
                              Case(When(eupmyendong_gubun='0',
                                        then=Value('')),
                                   When(eupmyendong_gubun='1',
                                        then=Concat(F('beopjeongeupmyendong_name'), Value(' '))),
                                   ),
                              Case(When(beopjeongri_name='', then=Value('')),
                                   default=Concat(F('beopjeongri_name'), Value(' '))),
                              'jibeonbonbeon_beonji',
                              Case(When(jibeonbubeon_ho=0, then=Value('')),
                                   default=Concat(Value('-'), F('jibeonbubeon_ho'), output_field=CharField())),
                              Value(' '), 'sigunguyong_building_name',
                              output_field=CharField())  # 지번 주소
        )

        query_set = query_set.filter(conditions)

        if only_count:
            return query_set.values('zip', 'doromyeong_addr', 'etc', 'jibun_addr').count()

        query_set = query_set.order_by('gichoguyeok_num', 'doromyeong', 'building_bonbeon')[offset: offset + limit + 1]

        return query_set

service = AddressService()
