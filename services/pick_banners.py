from models.pick_banners import PickBanner
from datetime import timedelta
from libs.utils import utc_now, local_now

class PickBannerService:
    def get_list(self, only_count=False, **kwargs):
        """
        Pick 배너 리스트
        """
        pick_id = kwargs.get('pick_id')

        banners = PickBanner.objects.filter(
            pick=pick_id,
            is_display=True
        ).select_related('pick')\
            .filter(
            pick__end_at__gte=(local_now().strftime('%Y%m%d%H%M%S'))
        )


        if only_count:
            return banners.count()

        banners = banners.order_by('-banner_id')

        results = banners.all()

        if not results:
            return {
                'list': [],
            }

        if not len(results):
            return {
                'list': [],
            }

        return {
            'list': results,
        }


service = PickBannerService()