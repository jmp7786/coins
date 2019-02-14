import re

from django.db.models import Q

from libs.aws.dynamodb import aws_dynamodb_etc_items
from models.stores import Store, Storebanner


class StoreService:
    def get_list(self, **kwargs):
        """
        스토어 리스트
        """

        query = kwargs.get('query')

        stores = Store.objects.filter(is_display='Y')

        if query:
            q = Q()
            word_list = re.findall('([\w.]+)', query)

            if len(word_list) < 1:
                return []
            elif len(word_list) == 1:
                if len(word_list[0]) == 1:
                    for sch_word in word_list:
                        q &= (Q(name=sch_word))
                else:
                    for sch_word in word_list:
                        q &= (Q(name__icontains=sch_word))
            else:
                for sch_word in word_list:
                    q &= (Q(name__icontains=sch_word))

            stores = Store.objects.filter(
                Q(is_display='Y') & q
            ).order_by(
                'name'
            )

        return stores

    def get_all_stores_by_dynamodb(self):
        """
        전체 스토어 리스트 ( dynamoDB )
        """
        items = aws_dynamodb_etc_items.get_stores()

        return [
            {
                'id': store.get('id_store'),
                'name': store.get('store_name'),
                'store_image': store.get('store_image'),
                'store_image_720': store.get('store_thumbnail')
            } for store in items]

    def get_store_banners(self, store_id):
        """
        스토어 배너
        """
        try:
            store = Store.objects.get(id=store_id)
        except Store.DoesNotExist:
            return None

        banners = Storebanner.objects.filter(
            is_display=True,
            store=store_id
        )

        setattr(store, 'banners', banners)
        setattr(store, 'banner_ratio', 0.405)

        return store


service = StoreService()
