from rest_framework.reverse import reverse
from copy import copy
from .test_utils import BaseAuthTest
from backends.api.v2.responses.faqs import FaqSerializer
from models.db_common.faqs import Faq
from functools import reduce


class TestFaqs(BaseAuthTest):
    faq_data = {
      "service_type_cd": "SV",
      "board_detail_type_cd": "BT02_01",
      "question": "앱 사용중 오류가 발생하였습니다. 어디에 보내야 하나요?",
      "answer": "더보기 > 1:1 문의하기 > 버그리포트를 선택하여 오류 사항을 작성하여 문의 등록해주세요.",
      "is_best": True,
      "created_id": 1234
    }

    def test_faqs_serializer(self):

        faq_data = copy(self.faq_data)
        serializer = FaqSerializer(data=faq_data)

        serializer.is_valid(raise_exception=True)
        faq = serializer.save()

        self.assertTrue(reduce(lambda x, y: x & y,
                               (getattr(faq, key) == value for key, value in faq_data.items())),
                        'Input Output 불일치'
                        )
        self.assertEqual(1, Faq.objects.count())

        response = self.client.get(reverse("faqs-list"), **self.auth_headers)
        self.assertEqual(response.status_code, 200,
                         'Expected Response Code 200, received {0} instead.'.format(response.status_code))

        self.assertEqual(response.data['count'], 1, '개수: %i' % response.data['count'])

    def test_auth(self):

        response = self.client.get(reverse("faqs-list"))
        self.assertEqual(response.status_code, 401,
                         'Expected Response Code 401, received {0} instead.'.format(response.status_code))



