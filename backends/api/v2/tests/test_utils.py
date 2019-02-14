from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from oauth2_provider.models import get_application_model
from oauth2_provider.compat import get_user_model
from oauth2_provider.settings import oauth2_settings
import json

Application = get_application_model()
UserModel = get_user_model()


class BaseAuthTest(APITestCase):
    def setUp(self):
        self.test_user = UserModel.objects.create_user("test_user", "test@user.com", "123456")
        self.dev_user = UserModel.objects.create_user("dev_user", "dev@user.com", "123456")

        oauth2_settings.ALLOWED_REDIRECT_URI_SCHEMES = ['http', 'custom-scheme']

        self.application = Application(
            name="Test Application",
            redirect_uris="http://localhost http://example.com http://example.it custom-scheme://example.com",
            user=self.dev_user,
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type="password",
        )
        self.application.save()

        oauth2_settings._SCOPES = ['read', 'write']
        oauth2_settings._DEFAULT_SCOPES = ['read', 'write']

        self.auth_headers = self.get_auth()

    def get_auth(self):

        token_request_data = {
            'username': "test_user",
            'password': "123456",
            'grant_type': 'password',
            'client_id': self.application.client_id,
            'client_secret': self.application.client_secret,
        }

        response = self.client.post(reverse('oauth2_provider:token'), data=token_request_data)
        content = json.loads(response.content.decode("utf-8"))
        auth_headers = {
            'AUTHORIZATION': 'Bearer ' + content['access_token'],
        }
        return auth_headers

    def tearDown(self):
        self.application.delete()
        self.test_user.delete()
        self.dev_user.delete()




