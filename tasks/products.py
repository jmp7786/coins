from celery import shared_task
from django.db.models import Case, IntegerField, Sum
from django.db.models import Q
from django.db.models import When

from libs.aws.dynamodb import aws_dynamodb_products
from libs.shortcuts import get_object_or_404
from models.products import Product
from models.reviews import Review


@shared_task
def update_product_info(product_id):
    """
    제품에 작성된 리뷰를 가지고 점수를 계산한다.
    """

    # product score update
    product = get_object_or_404(Product, id=product_id, is_display=True)

    reviews = Review.objects.filter(product=product, is_display=True, state='N', user__is_blinded=0)

    result = reviews.annotate(
        rating1=Case(When(rating=1, then=1), output_field=IntegerField(), default=0),
        rating2=Case(When(rating=2, then=1), output_field=IntegerField(), default=0),
        rating3=Case(When(rating=3, then=1), output_field=IntegerField(), default=0),
        rating4_1=Case(
            When(Q(rating=4, user__review_count__lte=1), then=1),
            output_field=IntegerField(), default=0
        ),
        rating4_2=Case(
            When(Q(rating=4, user__review_count__gt=1, user__review_count__lte=10), then=1),
            output_field=IntegerField(),
            default=0
        ),
        rating4_3=Case(
            When(Q(rating=4, user__review_count__gt=10, user__review_count__lt=30), then=1),
            output_field=IntegerField(),
            default=0
        ),
        rating4_4=Case(
            When(Q(rating=4, user__review_count__gte=30), then=1),
            output_field=IntegerField(),
            default=0
        ),
        rating5_1=Case(
            When(Q(rating=5, user__review_count__lte=1), then=1),
            output_field=IntegerField(),
            default=0
        ),
        rating5_2=Case(
            When(Q(rating=5, user__review_count__gt=1, user__review_count__lte=10), then=1),
            output_field=IntegerField(),
            default=0
        ),
        rating5_3=Case(
            When(Q(rating=5, user__review_count__gt=10, user__review_count__lt=30), then=1),
            output_field=IntegerField(),
            default=0
        ),
        rating5_4=Case(
            When(Q(rating=5, user__review_count__gte=30), then=1),
            output_field=IntegerField(),
            default=0
        ),
    ).aggregate(
        Sum('rating1'), Sum('rating2'), Sum('rating3'),
        Sum('rating4_1'), Sum('rating4_2'), Sum('rating4_3'), Sum('rating4_4'),
        Sum('rating5_1'), Sum('rating5_2'), Sum('rating5_3'), Sum('rating5_4')
    )

    rating1 = result['rating1__sum']
    rating2 = result['rating2__sum']
    rating3 = result['rating3__sum']

    rating4_1 = result['rating4_1__sum']
    rating4_2 = result['rating4_2__sum']
    rating4_3 = result['rating4_3__sum']
    rating4_4 = result['rating4_4__sum']

    rating5_1 = result['rating5_1__sum']
    rating5_2 = result['rating5_2__sum']
    rating5_3 = result['rating5_3__sum']
    rating5_4 = result['rating5_4__sum']

    # review count
    review_count = rating1 + rating2 + rating3 + \
                   rating4_1 + rating4_2 + rating4_3 + rating4_4 + \
                   rating5_1 + rating5_2 + rating5_3 + rating5_4

    # rating_avg
    rating_avg = (rating1 * 1.0 + rating2 * 2.0 + rating3 * 3.0 + (
        rating4_1 + rating4_2 + rating4_3 + rating4_4) * 4.0 + (
                      rating5_1 + rating5_2 + rating5_3 + rating5_4) * 5) / review_count
    rating_avg = round(rating_avg, 2)

    # product score
    converted_sum = rating1 * -20.0 + rating2 * -10.0 + rating3 * -1.0
    converted_sum += rating4_1 * 0.5 + rating4_2 * 2.5 + rating4_3 * 4.0 + rating4_4 * 5.0
    converted_sum += rating5_1 * 1.0 + rating5_2 * 5.0 + rating5_3 * 8.0 + rating5_4 * 10.0

    if review_count > 70:
        score = converted_sum / review_count * 70
    else:
        score = converted_sum

    review_count_score = review_count * 0.05 if review_count * 0.05 <= 50.0 else 50.0
    score += review_count_score
    score = round(score, 2)

    product.score = score
    product.review_count = review_count
    product.rating_avg = rating_avg
    product.save()

    # dynamo update
    attr_update = {'rating_avg': {'Value': {'N': str(product.rating_avg)}, 'Action': 'PUT'},
                   'review_count': {'Value': {'N': str(product.review_count)}, 'Action': 'PUT'}}
    aws_dynamodb_products.update(product_id, attr_update)

    return product_id