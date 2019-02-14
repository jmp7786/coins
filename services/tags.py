import re

from django.db.models import Q

from models.tags import Tag


class TagService:
    def get_list(self, only_count=False, **kwargs):
        limit = kwargs.get('limit', 20)
        cursor = kwargs.get('cursor')

        query = kwargs.get('query')

        tags = Tag.objects.filter(count__gt=0)

        if query:
            query_list = re.findall('([\w.]+)', query)

            if len(query_list) < 1:
                if only_count is True:
                    return 0
                return {
                    'list': [],
                    'next_offset': None,
                }

            q = Q()
            for sch_word in query_list:
                q &= Q(name__icontains=sch_word)

            tags = tags.filter(q)

        if only_count:
            return tags.count()

        tags = tags.order_by('-count', '-create_date')

        cursor = int(cursor or 1)
        offset = (cursor - 1) * limit
        results = tags.all()[offset: offset + limit + 1]

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
            next_offset = cursor + 1
            del results[-1]
        else:
            next_offset = None

        return {
            'list': results,
            'next_offset': next_offset,
        }


service = TagService()
