from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler

from libs.slack import Field
from libs.slack.hooks import DjangoExceptionHook
from libs.utils import get_exception_message


class Error(object):
    NOT_FOUND = "404"
    BAD_REQUEST = "400"
    MISSING_PARAMETER = "400.0001"
    INVALID_PARAMETER = "400.0002"


class GlowpickAPIException(APIException):
    e_code = None
    message = None
    detail = None

    def __init__(self, message=None, *args, **kwargs):
        if self.e_code and self.message and self.detail:
            self.default_detail = {'code': self.e_code,
                                   'message': self.message,
                                   'detail': self.detail}
        if message is not None:
            if 'message' in self.default_detail:
                self.default_detail.update({'message': message})
            else:
                self.default_detail = {'message': message}
        super(GlowpickAPIException, self).__init__(*args, **kwargs)


class NotFoundException(GlowpickAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    e_code = Error.NOT_FOUND
    message = "Not Found"
    detail = "Not Found"


class BadRequestException(GlowpickAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    e_code = Error.BAD_REQUEST
    message = "Bad Request"
    detail = "Bad Request"


class MissingParameterException(BadRequestException):
    status_code = status.HTTP_400_BAD_REQUEST
    e_code = Error.MISSING_PARAMETER
    message = "Missing Parameter"
    detail = "Missing Parameter"


class InvalidParameterException(BadRequestException):
    status_code = status.HTTP_400_BAD_REQUEST
    e_code = Error.INVALID_PARAMETER
    message = "Invalid Parameter"
    detail = "Invalid Parameter"


class ForbiddenException(GlowpickAPIException):
    status_code = status.HTTP_403_FORBIDDEN
    e_code = "403.0001"
    message = 'forbidden'
    detail = 'forbidden'


class ConflictException(GlowpickAPIException):
    status_code = status.HTTP_409_CONFLICT
    e_code = "409"
    message = "Conflict"
    detail = "Conflict"


class FailedDependencyException(GlowpickAPIException):
    status_code = status.HTTP_424_FAILED_DEPENDENCY
    e_code = "424"
    message = "Failed Dependency"
    detail = "Failed Dependency"

class FailedPreconditionException(GlowpickAPIException):
    status_code = status.HTTP_412_PRECONDITION_FAILED
    e_code = "412"
    message = "Precondition Failed"
    detail = "Precondition Failed"


class InternalServerException(GlowpickAPIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    e_code = "500"
    message = "Internal Server Error"
    detail = "Internal Server Error"

class ServiceUnavailableException(GlowpickAPIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    e_code = "503"
    message = "Service Unavailable"
    detail = "Service Unavailable"


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    if settings.DEBUG and \
            (not response or response.status_code not in [status.HTTP_400_BAD_REQUEST, \
                                                          status.HTTP_401_UNAUTHORIZED]):
        return response

    if response is None:
        exc = GlowpickAPIException()
        response = exception_handler(exc, context)
        response.data['code'] = response.status_code
        response.data['message'] = str(exc)
    else:
        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            response.data['code'] = response.status_code
            response.data['message'] = response.data['detail']

        if response.status_code == status.HTTP_400_BAD_REQUEST \
                and 'code' not in response.data:
            response.data['code'] = response.status_code
            response.data['message'] = "Invalid Parameter"

    if not settings.DEBUG and (response.status_code >= 300 and response.status_code != status.HTTP_401_UNAUTHORIZED
                               and response.status_code != status.HTTP_409_CONFLICT
                               and response.status_code != status.HTTP_400_BAD_REQUEST
                               and response.status_code != status.HTTP_404_NOT_FOUND
                               ):
        message = get_exception_message(context)
        slack_django = DjangoExceptionHook()
        fields = [Field(message['body'], message['desc'])]
        slack_django.set_attachment(pretext=message['title'], fields=fields)
        slack_django.send()
    return response
