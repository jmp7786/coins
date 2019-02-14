from rest_framework.reverse import reverse
from .test_utils import BaseAuthTest
from ..responses.inquiries import InquirySerializer
from functools import reduce
from rest_framework.exceptions import ValidationError
from copy import copy


class TestInquiries(BaseAuthTest):
    inquiry_data = {"name": "name",
                        "content": "testetewr",
                        "email": "sing@sdf.com",
                        "service_type_cd": "SV",
                        "board_type_cd": "BT03",
                        "board_detail_type_cd": "BT03_01",
                        "contact": "sfsdf",
                        "customer_id": 123,
                        }

    def test_inquiry_serializer_is_answered(self):
        inquiry_data = copy(self.inquiry_data)

        serializer = InquirySerializer(data=inquiry_data)
        serializer.is_valid(raise_exception=True)
        self.assertEqual(serializer.data['is_answered'], False,
                         'Expected is_answered False, received {0} instead.'.format(serializer.data['is_answered']))

    def test_inquiry_serializer_validate(self):

        inquiry_data = copy(self.inquiry_data)
        inquiry_data['board_type_cd'] = 'BT04'
        serializer = InquirySerializer(data=inquiry_data)

        with self.assertRaisesRegex(ValidationError, 'BT04'):
            serializer.is_valid(raise_exception=True)

        inquiry_data = copy(self.inquiry_data)
        inquiry_data['board_detail_type_cd'] = 'BT04_01'
        serializer = InquirySerializer(data=inquiry_data)

        with self.assertRaisesRegex(ValidationError, 'BT04_01'):
            serializer.is_valid(raise_exception=True)

    def test_inquiry_serializer_product_validate(self):

        inquiry_data = copy(self.inquiry_data)
        inquiry_data['service_type_cd'] = 'EC'
        inquiry_data['board_type_cd'] = 'BT04'
        inquiry_data['board_detail_type_cd'] = 'BT04_01'
        serializer = InquirySerializer(data=inquiry_data)

        with self.assertRaisesMessage(ValidationError, 'product_name'):
            serializer.is_valid(raise_exception=True)
        with self.assertRaisesMessage(ValidationError, 'product_id'):
            serializer.is_valid(raise_exception=True)
        with self.assertRaisesMessage(ValidationError, 'product_code'):
            serializer.is_valid(raise_exception=True)
        with self.assertRaisesMessage(ValidationError, 'product_image_url'):
            serializer.is_valid(raise_exception=True)

    def test_inquiry_serializer_company_validate(self):

        inquiry_data = copy(self.inquiry_data)
        inquiry_data['service_type_cd'] = 'SV'
        inquiry_data['board_type_cd'] = 'BT03'
        inquiry_data['board_detail_type_cd'] = 'BT03_04'
        serializer = InquirySerializer(data=inquiry_data)

        with self.assertRaisesMessage(ValidationError, 'company_name'):
            serializer.is_valid(raise_exception=True)

    def test_inquiry_serializer_save(self):

        serializer = InquirySerializer(data=self.inquiry_data)
        serializer.is_valid(raise_exception=True)
        inquiry = serializer.save()

        self.assertTrue(reduce(lambda x, y: x & y, map(lambda x: x[1] == getattr(inquiry, x[0]),
                                                       self.inquiry_data.items())),
                        'Input Output 불일치'
                        )

    def test_create_inquiries(self):
        response = self.client.post(reverse('inquiries-list'), self.inquiry_data, **self.auth_headers)
        self.assertEqual(response.status_code, 201,
                         'Expected Response Code 201, received {0} instead.'.format(response.status_code))

        inquiry_data = copy(self.inquiry_data)
        inquiry_data['service_type_cd'] = 'SV'
        inquiry_data['board_type_cd'] = 'BT03'
        inquiry_data['board_detail_type_cd'] = 'BT03_04'
        response = self.client.post(reverse('inquiries-list'), inquiry_data, **self.auth_headers)
        self.assertEqual(response.status_code, 400,
                         'Expected Response Code 400, received {0} instead.'.format(response.status_code))
        inquiry_data['company_name'] = "apple"
        response = self.client.post(reverse('inquiries-list'), inquiry_data, **self.auth_headers)
        self.assertEqual(response.status_code, 201,
                         'Expected Response Code 201, received {0} instead.'.format(response.status_code))

        inquiry_data = copy(self.inquiry_data)
        inquiry_data['service_type_cd'] = 'EC'
        inquiry_data['board_type_cd'] = 'BT04'
        inquiry_data['board_detail_type_cd'] = 'BT04_01'
        response = self.client.post(reverse('inquiries-list'), inquiry_data, **self.auth_headers)
        self.assertEqual(response.status_code, 400,
                         'Expected Response Code 400, received {0} instead.'.format(response.status_code))

        inquiry_data['product_id'] = 123
        inquiry_data['product_code'] = 'product_code'
        inquiry_data['product_name'] = 'product_name'
        inquiry_data['product_image_url'] = 'https://docs.djangoproject.com/en/1.11/topics/http/urls/#reverse'
        response = self.client.post(reverse('inquiries-list'), inquiry_data, **self.auth_headers)
        self.assertEqual(response.status_code, 201,
                         'Expected Response Code 201, received {0} instead.'.format(response.status_code))

    def test_create_inquiry_without_customer_id(self):

        inquiry_data = {
            "board_detail_type_cd": "BT03_01",
            "board_type_cd": "BT03",
            "contact": "123123",
            "content": "asdasd",
            "email": "asd@asd.cmo",
            "environment_info": "string",
            "is_email": True,
            "is_sms": False,
            "name": "asd",
            "service_type_cd": "SV"
        }
        response = self.client.post(reverse('inquiries-list'), inquiry_data, **self.auth_headers)
        self.assertEqual(response.status_code, 201,
                         'Expected Response Code 201, received {0} instead.'.format(response.status_code))
        response = self.client.get(reverse("inquiries-list"), data={"board_detail_type_cd": "BT03_01"}, **self.auth_headers)
        self.assertEqual(response.status_code, 200,
                         'Expected Response Code 200, received {0} instead.'.format(response.status_code))

        self.assertEqual(response.data['count'], 4, '문의 개수: %i' % response.data['count'])

    def test_delete_inquiry(self):
        response = self.client.get(reverse("inquiries-list"), **self.auth_headers)

        inquiry_count = response.data['count']
        response = self.client.delete(reverse('inquiries-detail',
                                              kwargs={'pk': response.data['results'][0]['id']}),
                                      **self.auth_headers)
        self.assertEqual(response.status_code, 204,
                         'Expected Response Code 200, received {0} instead.'.format(response.status_code))
        response = self.client.get(reverse("inquiries-list"), **self.auth_headers)

        self.assertEqual(response.data['count'], inquiry_count-1, '문의 개수: %i' % response.data['count'])

    def test_is_answered_default_false(self):

        inquiry_data = {
            "board_detail_type_cd": "BT03_01",
            "board_type_cd": "BT03",
            "contact": "123123",
            "content": "asdasd",
            "email": "asd@asd.cmo",
            "environment_info": "string",
            "is_email": True,
            "is_sms": False,
            "name": "asd",
            "service_type_cd": "SV"
        }
        response = self.client.post(reverse('inquiries-list'), inquiry_data, **self.auth_headers)
        self.assertEqual(response.status_code, 201,
                         'Expected Response Code 201, received {0} instead.'.format(response.status_code))

        self.assertEqual(response.data['is_answered'], False,
                         'Expected is_answered False, received {0} instead.'.format(response.data['is_answered']))

    def test_inquiries_order(self):

        response = self.client.get(reverse("inquiries-list"), **self.auth_headers)
        results = copy(response.data['results'])
        results.sort(key=lambda result: result['created_at'], reverse=True)
        self.assertEqual(results, response.data['results'],
                         'Response not ordered by created_at')

    def test_auth(self):

        response = self.client.get(reverse("inquiries-list"))
        self.assertEqual(response.status_code, 401,
                         'Expected Response Code 401, received {0} instead.'.format(response.status_code))

