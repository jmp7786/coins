from rest_framework.reverse import reverse
from .test_utils import BaseAuthTest


class TestCateogires(BaseAuthTest):
    def test_auth(self):
        response = self.client.get(reverse("categories-list"))
        self.assertEqual(
            response.status_code, 401,
            'Expected Response Code 401, received {0} instead.'.format(response.status_code)
        )

    def test_call_list(self):
        response = self.client.get(reverse("categories-list"), **self.auth_headers)
        self.assertEqual(
            response.status_code, 200,
            'Expected Response Code 200, received {0} instead.'.format(response.status_code)
        )

    def test_call_products(self):
        response = self.client.get(reverse("categories-products", kwargs={'pk': 2}), **self.auth_headers)
        self.assertEqual(
            response.status_code, 404,
            'Expected Response Code 200, received {0} instead.'.format(response.status_code)
        )
