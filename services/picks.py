from datetime import timedelta

from django.db.models import F

from libs.utils import local_now
from models.pick_categories import PickCategory
from models.picks import Pick
from models.users import User


class PickService:
    def get_list(self, **kwargs):
        limit = kwargs.get('limit', 20)
        cursor = kwargs.get('cursor')
        category_id = kwargs.get('category_id')

        base = Pick.objects.filter(category__is_display=True)
        cursor = int(cursor or 1)
        offset = (cursor - 1) * limit

        if category_id:
            base = base.filter(category=category_id)
        base = base.order_by('-seq')

        results = base.all()[offset: offset + limit + 1]
        if cursor != 1:
            categories = None
        else:
            c = PickCategory.objects.order_by('seq').values()[:15]

            total_new = False

            for item in c:
                date_days_ago = local_now() - timedelta(days=3)
                date_days_ago = date_days_ago.strftime('%Y%m%d%H%M%S')
                pick_last = Pick.objects.filter(category=item['category_id']).filter(_created_at__gte=date_days_ago)

                if pick_last:
                    item['is_new'] = True
                    total_new = True
                else:
                    item['is_new'] = False

            categories = [{
                'category_id': 0,
                'name': '전체 캐스트 보기',
                'is_new': total_new
            }]

            categories += c

        next_offset = None
        if len(results) == limit + 1:
            results = list(results)
            next_offset = cursor + 1
            del results[-1]

        return {
            'picks': results,
            'categories': categories,
            'next_offset': next_offset,
        }

    def get_user_pick_categories(self, user_id):
        """
        유저가 좋아요 한 캐스트(픽)이 포함된 카테고리 리스트
        """
        picks = User.objects.get(id=user_id).picks.all()
        picks = picks.filter(is_display=True, category__is_display=True).order_by('category__seq')
        pick_categories = picks.values('category', 'category__name').distinct()
        categories = list()
        categories.append({
            'category_id': 0,
            'name': '전체 캐스트',
        })
        for category in pick_categories.iterator():
            categories.append({'category_id': category['category'], 'name': category['category__name']})
        return categories

    def get_user_picks(self, user_id, **kwargs):
        """
        유저가 좋아요 한 캐스트(픽) 리스트
        """
        limit = kwargs.get('limit', 20)
        cursor = kwargs.get('cursor')
        category_id = kwargs.get('category_id')

        picks = User.objects.get(id=user_id).picks.all()
        picks = picks.filter(is_display=True)

        if category_id and category_id != 0:
            picks = picks.filter(category=category_id)

        total_count = None

        if cursor is None:
            total_count = picks.count()

        picks = picks.order_by('-picklike__id')

        if cursor:
            picks = picks.annotate(picklike__id=F('picklike__id'))
            picks = picks.filter(picklike__id__lt=cursor)

        results = picks.all()[:limit + 1]

        if len(results) == limit + 1:
            results = list(results)
            next_offset = results[-2].picklike_set.get(user=user_id, pick=results[-2].pick_id).id
            del results[-1]
        else:
            next_offset = None

        return results, total_count, next_offset

    def increase_hits_count(self, pick_id):
        pick = Pick.objects.get(pick_id=pick_id)
        pick.hits_count += 1
        pick.save()
        return pick.hits_count
    
service = PickService()
