from rest_framework import routers
from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response

from backends.api.v2.responses.addresses import AddressResponse
from services.addresses import service as addresses_service
from .forms.addresses import AddressForm


class AddressView(viewsets.ViewSet):
    def list(self, request):
        params = AddressForm(data=request.GET)
        params.is_valid(raise_exception=True)

        limit = int(params.data.get('limit', 100) or 100)
        cursor = params.data.get('cursor', 1)
        cursor = int(cursor or 1)

        response = dict()

        if cursor == 1:
            response['total_count'] = addresses_service.get_list(params, only_count=True)

        addresses = AddressResponse(addresses_service.get_list(params), many=True)
        response['addresses'] = addresses.data

        if len(response['addresses']) == limit + 1:
            next_offset = cursor + 1
            del response['addresses'][-1]
        else:
            next_offset = None

        response['paging'] = dict()
        if next_offset:
            response['paging']['next'] = next_offset

        return Response(response, status=status.HTTP_200_OK)


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'addresses', AddressView, base_name='addresses')
