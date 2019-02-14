from models.blinded_reviews import BlindedReview


class BlindedReviewService:
    def get(self, review_id):
        """
        :param int review_id: 댓글 id(필수)
        """
        return BlindedReview.objects.filter(review=review_id)


service = BlindedReviewService()
