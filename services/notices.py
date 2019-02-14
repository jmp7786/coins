from models.db_common.notices import Notice
from models.db_common.common_codes import CommonCodeValues


class NoticeService:
    def get_categories(self):
        return CommonCodeValues.objects.filter(
            common_codes__common_cd_value='board_category_cd'
        ).order_by('sort_order')

    def get_list(self, params, only_count=None):
        cursor = params.data.get('cursor')
        limit = params.data.get('limit')
        offset = (cursor - 1) * limit
        type_cd = params.data.get('board_type')
        category_cd = params.data.get('board_category')

        query_set = Notice.objects.filter(is_display=True)
        if type_cd:
            query_set = query_set.filter(board_type_cd=type_cd)

        if category_cd:
            query_set = query_set.filter(board_category_cd=category_cd)

        if only_count:
            return query_set.count()

        query_set = query_set[offset: offset + limit + 1]

        return query_set


service = NoticeService()
