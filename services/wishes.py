from enum import Enum

from django.db.models import F

from models.users import User


class Sort(Enum):
    rating_avg_desc = 'high_rating'
    rating_avg_asc = 'low_rating'
    create_date_desc = 'latest'
    create_date_asc = 'oldest'


class WishService:
    def get_list(self, user_id, only_count=False, **kwargs):
        limit = kwargs.get('limit', 20)
        cursor = kwargs.get('cursor')
        order = kwargs.get('order')

        store_id = kwargs.get('store_id')
        main_category_id = kwargs.get('main_category_id')
        sub_category_id = kwargs.get('sub_category_id')
        brand_category_id = kwargs.get('brand_category_id')
        brand_id = kwargs.get('brand_id')

        is_commerce = kwargs.get('is_commerce')

        wishes = User.objects.get(id=user_id).wishes
        wishes = wishes.filter(is_display=True).select_related('brand', 'productgoods')

        if store_id and store_id != 'all':
            stores = store_id.split(",")
            for store_id in stores:
                wishes = wishes.filter(storesproducts__store=store_id)

        if sub_category_id and sub_category_id != 0:
            wishes = wishes.filter(categories=sub_category_id)
        else:
            if main_category_id and main_category_id != 0:
                wishes = wishes.filter(categories__main_category=main_category_id)

        if brand_id and brand_id != 0:
            wishes = wishes.filter(brand=brand_id)
        else:
            if brand_category_id and brand_category_id != 0:
                wishes = wishes.filter(brand__brandcategories__brand_category=brand_category_id)

        if is_commerce:
            wishes = wishes.filter(productgoods__goods_count__gt=0)

        if only_count:
            return wishes.all().count()

        default_sort = Sort.create_date_desc.value
        sort = Sort[order].value if order else default_sort

        if sort == 'high_rating':
            wishes = wishes.order_by('-rating_avg', '-wish__create_date')
        elif sort == 'low_rating':
            wishes = wishes.order_by('rating_avg', '-wish__create_date')
        elif sort == 'latest':
            wishes = wishes.order_by('-wish__id')
        elif sort == 'oldest':
            wishes = wishes.order_by('wish__id')

        if cursor and sort == 'latest':
            wishes = wishes.annotate(wish_id=F('wish__id'))
            wishes = wishes.filter(wish_id__lt=cursor)

        results = wishes.all().distinct()[:limit + 1]

        if sort != 'latest':
            cursor = int(cursor or 1)
            offset = (cursor - 1) * limit
            results = wishes.all()[offset: offset + limit + 1]

        if len(results) == limit + 1:
            results = list(results)
            if sort == 'latest':
                next_offset = results[-2].wish_set.get(user=user_id, product=results[-2].id).id
            else:
                next_offset = cursor + 1
            del results[-1]
        else:
            next_offset = None

        return results, next_offset


service = WishService()
