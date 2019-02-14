from models.products import Product


class PickProductService:
    def get_list(self, only_count=False, **kwargs):
        """
        Pick 제품 리스트
        """
        pick_id = kwargs.get('pick_id')
        limit = kwargs.get('limit', 20)
        cursor = kwargs.get('cursor')

        products = Product.objects.filter(
            pickproducts__pick=pick_id,
            is_display=True
        ).select_related('brand')

        if only_count:
            return products.count()

        products = products.order_by('-id')

        if cursor:
            products = products.filter(id__lt=cursor)

        results = products.all()[:limit + 1]

        if not results:
            return {
                'list': [],
                'next_offset': None,
            }

        if not len(results):
            return {
                'list': [],
                'next_offset': None,
            }

        if len(results) == limit + 1:
            results = list(results)
            next_offset = results[-2].id
            del results[-1]
        else:
            next_offset = None

        return {
            'list': results,
            'next_offset': next_offset,
        }


service = PickProductService()