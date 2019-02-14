from models.events import EventComment


class EventCommentService:
    def get_list(self, event_id, **kwargs):
        limit = kwargs.get('limit', 20)
        cursor = kwargs.get('cursor')

        comments = EventComment.objects.filter(
            event=event_id,
            is_display=True
        ).select_related(
            'user'
        )

        cursor = int(cursor or 1)
        offset = (cursor - 1) * limit
        comment_list = comments.all()
        count = len(comment_list)
        results = comment_list[offset: offset + limit + 1]


        for idx, val in enumerate(results):
            results[idx].comment_id  = val.id
        if not results:
            return {
                'list': [],
                'next_offset': None,
                'count': 0
            }

        if not len(results):
            return {
                'list': [],
                'next_offset': None,
                'count': 0
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
            'count': count
        }


service = EventCommentService()
