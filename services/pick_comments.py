from backends.common.exceptions import NotFoundException, ForbiddenException
from models.pick_comments import PickComment


class PickCommentService:
    def get_list(self, only_count=False, **kwargs):
        """
        Pick 댓글 리스트
        """
        pick_id = kwargs.get('pick_id')

        limit = kwargs.get('limit', 20)
        cursor = kwargs.get('cursor')

        comments = PickComment.objects.filter(
            pick=pick_id,
            is_display=True
        ).select_related(
            'user'
        )

        if only_count:
            return comments.count()

        comments = comments.order_by('-id')

        if cursor:
            comments = comments.filter(id__lt=cursor)

        results = comments.all()[:limit + 1]

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

    def remove_comment(self, comment_id, user_id):
        """
        Pick 댓글 삭제

        :param int comment_id: 댓글 id(필수)
        :param int user_id: 사용자 id (필수)
        """
        try:
            comment = PickComment.objects.get(id=comment_id)
        except PickComment.DoesNotExist:
            raise NotFoundException("No PickComment")

        if comment.user.id != user_id:
            raise ForbiddenException()

        comment.delete()


service = PickCommentService()
