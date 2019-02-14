import logging
import random

from dateutil.relativedelta import relativedelta
from rest_framework import routers
from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response
from cacheback.base import Job

from libs.aws.dynamodb import aws_dynamodb_etc_items
from libs.utils import iso8601, local_now, get_this_week
from libs.utils import request_ads, is_filtered_version
from models.banners import Banner
from models.db_common.notices import Notice
from models.events import Event
from models.picks import Pick
from models.products import Product
from services.events import service as event_service
from services.products import service as product_service
from .forms.common import CursorForm
from .responses.mains import MainHomeResponse

logger = logging.getLogger(__name__)


class MainCache(Job):
    lifetime = 60
    fetch_on_stale_threshold = True

    def fetch(self, cursor):
        response = None
        if cursor == 1:
            response = {
                'top_banners': Banner.objects.filter(banner_type='MAIN').order_by('seq', '?').all()[:20],
                'weekly_rankings': {
                    'counted_at': iso8601(get_this_week(is_strformat=False)),
                    'categories': product_service.get_weekly_ranking()
                },
                'ongoing_events': {
                    'total_count': Event.objects.ongoing().filter(is_evaluated=True).count(),
                    'events': event_service.get_ongoing_evaluation_events(3)
                },
                'store_button': aws_dynamodb_etc_items.get_store_button(),
                'paging': {'next': 2}
            }

        elif cursor == 2:
            this_month = local_now().strftime("%Y%m")
            new_products_count = Product.objects.new_products(this_month).count()
            if not new_products_count:
                this_month = (local_now() - relativedelta(months=1)).strftime("%Y%m")
            response = {
                'recent_notice': Notice.objects.first(),
                'new_products': {
                    'total_count': Product.objects.new_products(this_month).count(),
                    'items': product_service.get_new_products(this_month, 6)},
                'picks': Pick.objects.order_by('-seq').all()[:5],
                'paging': {'next': None}
            }
        return response


_main_cache = MainCache()


class MainView(viewsets.ViewSet):
    # permission_classes = (CustomIsAuthenticated,)
    authentication_classes = ()

    @list_route(methods=['GET'])
    def home(self, request):

        forms = CursorForm(data=request.GET)
        forms.is_valid(raise_exception=True)

        cursor = int(request.GET.get('cursor') or 1)

        response = _main_cache.get(cursor)
        top_banners = response.get('top_banners')
        if top_banners:
            try:
                os_info = request.META.get('HTTP_OS')
                appversion = request.META.get('HTTP_APPVERSION')

                if not is_filtered_version(os_info, appversion):
                    # need some link_target to be replaced
                    for b in top_banners:
                        if (b.link_type >= 34) and (b.link_type <= 41):
                            # forward EC link_target to APP installtation
                            b.link_type = 14
                            b.link_target = "http://resource.glowpick.com/common/guide-update/"
            except Exception as e:
                logger.error(e)

            response['top_banners'] = sorted(
                top_banners,
                key=lambda k: (k.seq + 1, ((k.seq + 1) * random.random()))
            )

        # For requesting Ads
        top_banners = response.get('top_banners')
        ongoing_events = response.get('ongoing_events')
        picks = response.get('picks')
        new_products = response.get('new_products')

        if top_banners:
            banner_ids = ",".join([str(banner.id) for banner in top_banners])
            request_ads('GP0001', banner_ids)

        if ongoing_events and ongoing_events.get('events'):
            events = ongoing_events.get('events')
            event_ids = ",".join([str(event.id) for event in events])
            request_ads('GP0008', event_ids)

        if picks:
            pick_ids = ",".join([str(pick.pick_id) for pick in picks])
            request_ads('GP0007', pick_ids)

        if new_products and new_products.get('items'):
            ads = new_products.get('items')
            ad_ids = ",".join([str(ad.id) for ad in ads if not isinstance(ad, dict)])
            request_ads('GP0002', ad_ids)

        return Response(MainHomeResponse(response).data)


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'main', MainView, base_name='main')
