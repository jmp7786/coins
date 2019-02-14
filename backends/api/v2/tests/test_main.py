from rest_framework.reverse import reverse
from rest_framework.test import APITestCase


class TestMain(APITestCase):

    def test_main(self):
        response = self.client.get(reverse('main-home'))

        self.assertEqual(response.status_code, 200,
                         'Expected Response Code 200, received {0} instead.'.format(response.status_code))
