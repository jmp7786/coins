from rest_framework.reverse import reverse
from .test_utils import BaseAuthTest
import json


class TestPicks(BaseAuthTest):

    def test_pick(self):

        response = self.client.get(reverse("picks-detail", kwargs={'pk': 512}), **self.auth_headers)
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(response.status_code, 200,
                    'Expected Response Code 200, received {0} instead.'.format(response.status_code))