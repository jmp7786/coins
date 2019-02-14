import json
from collections import OrderedDict
from datetime import datetime
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from rest_framework import routers
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response

from backends.api.exceptions import ConflictException, InvalidParameterException
from libs.aws.utils import send_push_message
from libs.elasticsearch.reviews import elasticsearch_reviews
from libs.oauth2.permissions import CustomIsAuthenticated
from libs.shortcuts import get_object_or_404
from libs.utils import get_client_ip, extract_tags, local_now,\
    format_round_datetime, iso8601
from cash_db.redis_utils import get_review_is_written, set_review_is_written, \
    period_zincrby, period_zrem, period_hset
from libs.utils import utc_now
from django.db.utils import IntegrityError
from models.blinded_reviews import BlindedReview
from models.common_codes import CommonCode
from models.events import EventPrizeMapping
from models.messages import MessageBox, MessageCategory
from models.product_goods import ProductGoods
from models.products import Product
from models.reviews import Review
from models.reviews import Reviewlike
from models.reviews import Review_first_log
from models.tags import Tag, TagObject
from models.users import User
from services.blinded_reviews import service as blinded_review_service
from services.reviews import service as review_service
from services.users import service as users_service
from tasks.products import update_product_info
from .forms.reviews import ReviewsForm, ReviewCheckForm, ReviewWriteForm, ReviewUpdateForm, ReviewReportForm
from .responses.common import SuccessMessageResponse
from .responses.reviews import ReviewsResponse, ReivewCheckResponse, ReviewWriteResponse, ReportTypesResponse, ReivewCheckRankRangeResponse


class ReviewView(viewsets.ViewSet):
    permission_classes = (CustomIsAuthenticated,)

    parameter_classes = {
        'get_list': ReviewsForm,
        'get_check': ReviewCheckForm,
        'post_create': ReviewWriteForm,
        'put_update': ReviewUpdateForm,
        'post_reports': ReviewReportForm,
    }

    response_docs = {
        'get_list': {
            '200': {
                'description': '리뷰 리스트',
                'schema': {
                    'type': 'object',
                    'properties': ReviewsResponse,
                }
            },
            '400': {
                'description': 'Invalid Parameters',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'detail': {
                            'type': 'string',
                        },
                        'message': {
                            'type': 'string'
                        },
                        'code': {
                            'type': 'string'
                        }
                    }
                },
            }
        },
        'get_check': {
            '200': {
                'description': '리뷰 작성 확인',
                'schema': {
                    'type': 'object',
                    'properties': ReivewCheckResponse,
                }
            },
            '400': {
                'description': 'Invalid Parameters',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'detail': {
                            'type': 'string',
                        },
                        'message': {
                            'type': 'string'
                        },
                        'code': {
                            'type': 'string'
                        }
                    }
                },
            },
            '404': {
                'description': 'Not found',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'detail': {
                            'type': 'string'
                        },
                        'message': {
                            'type': 'string'
                        },
                        'code': {
                            'type': 'string'
                        }
                    }
                },
            }
        },
        'post_create': {
            '201': {
                'description': '리뷰 작성',
                'schema': {
                    'type': 'object',
                    'properties': ReviewWriteResponse,
                }
            },
        },
        'post_like': {
            '200': {
                'description': '리뷰 좋아요',
                'schema': {
                    'type': 'object',
                    'properties': SuccessMessageResponse,
                }
            },
            '400': {
                'description': 'Invalid Parameters',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'detail': {
                            'type': 'string',
                        },
                        'message': {
                            'type': 'string'
                        },
                        'code': {
                            'type': 'string'
                        }
                    }
                },
            },
            '404': {
                'description': 'Not found',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'detail': {
                            'type': 'string'
                        },
                        'message': {
                            'type': 'string'
                        },
                        'code': {
                            'type': 'string'
                        }
                    }
                },
            }
        },
        'get_report_types': {
            '200': {
                'description': '신고 유형 목록',
                'schema': {
                    'type': 'object',
                    'properties': ReportTypesResponse,
                }
            },
        },
    }

    def list(self, request):
        """
        리뷰 리스트 (검색)
        """

        # 파라미터
        params = ReviewsForm(data=request.GET)
        params.is_valid(raise_exception=True)

        cursor = params.validated_data.get('cursor')
        has_top_reviewers = params.validated_data.get('top_reviewers')

        data = dict()
        try:
            results = review_service.get_list_elacticsearch(**params.validated_data)
            if results:
                data['reviews'] = results.get('review_list')
                next_offset = results.get('next_offset')
                if cursor is None:
                    data['total_count'] = results['total_count']
                data['paging'] = dict()
                if next_offset:
                    data['paging']['next'] = next_offset
        except:
            review_service.setter()
            results = review_service.get_list(**params.validated_data)
            if results:
                data['reviews'] = results.get('list')
                next_offset = results.get('next_offset')

                # TODO very slow query (조건에 맞는 리뷰의 전체 수)
                if cursor is None:
                    data['total_count'] = review_service.get_list(only_count=True)

                data['paging'] = dict()
                if next_offset:
                    data['paging']['next'] = next_offset

        if has_top_reviewers and cursor is None:
            try:
                if params.validated_data.get('order') == 'create_date_desc' \
                        and params.validated_data.get('age') == 'all' \
                        and params.validated_data.get('gender') == 'all' \
                        and params.validated_data.get('rating') == 'all' \
                        and params.validated_data.get('skin_type') == 'all':
                    data['top_reviewers'] = users_service.get_top_users_by_dynamo()
                else:
                    if params.validated_data['order'] == 'create_date_desc' \
                            or params.validated_data['order'] == 'create_date_asc':
                        params.validated_data['order'] = 'top_ranking'
                    data['top_reviewers'] = users_service.get_list(top3=True, **params.validated_data).get('list')
            except:
                if params.validated_data['order'] == 'create_date_desc' \
                        or params.validated_data['order'] == 'create_date_asc':
                    params.validated_data['order'] = 'top_ranking'
                data['top_reviewers'] = users_service.get_list(top3=True, **params.validated_data).get('list')

        # 응답
        response = ReviewsResponse(data).data

        return Response(response, status=status.HTTP_200_OK)

    def create(self, request):
        """
        새 리뷰 작성
        ---

        <br>
        <b>헤더</b>
        - IDREGISTER:        (필수) 회원 항번 <br>
        """

        # parameters
        cuid = int(request.META.get('HTTP_IDREGISTER') or 0)
        user = get_object_or_404(User, id=cuid)

        review_service.reset_rank(cuid)
        
        params = ReviewWriteForm(data=request.data)
        params.is_valid(raise_exception=True)

        if user.gender is None or user.skin_type is None or user.birth_year is None:
            raise InvalidParameterException(
                _("내정보에서 추가정보를 입력하셔야 작성이 가능합니다.")
            )

        client_ip = get_client_ip(request)
        contents = params.validated_data.get('contents')
        rating = params.validated_data.get('rating')
        product_id = params.validated_data.get('product_id')
        product = get_object_or_404(Product, id=product_id, is_display=True)

        if Review.objects.filter(user=cuid, product=product_id).exists():
            raise ConflictException(
                _("이미 리뷰를 작성한 제품입니다.")
            )

        with transaction.atomic():
            # review insert
            now = local_now().strftime('%Y%m%d%H%M%S')
            review = Review(user=user, product=product, rating=rating, contents=contents, ip_address=client_ip,
                            is_display=True, is_evaluation=False, _created_at=now)

            # 평가단 여부 확인
            if EventPrizeMapping.objects.filter(
                    user=user, product=product
            ).filter(
                event__activity_date__gte=local_now().strftime('%Y%m%d%H%M%S')
            ).exists():
                review.is_evaluation = True

            review.save()

            # user info update
            user.review_count += 1
            user.score += 1
            user.save()

            # product info update
            update_product_info.delay(product_id)

            # tag update
            tags = extract_tags(contents)
            for tag_name in tags:
                tag, created = Tag.objects.get_or_create(name=tag_name)
                if created:
                    TagObject(type='review', object_id=review.id, tag=tag).save()
                    tag.create_date = now
                    tag.save()
                else:
                    if not TagObject.objects.filter(type='review', object_id=review.id, tag=tag).exists():
                        TagObject(type='review', object_id=review.id, tag=tag).save()
                        tag.count += 1
                        tag.modified_date = now
                        tag.save()

            review.tag = ",".join(tags)
            review.save()

            # elastic update
            body = dict()
            # review
            body['idreviewcomment'] = review.id
            body['reviewText'] = contents
            body['rating'] = rating
            body['likeCount'] = 0
            body['isDisplay'] = 1
            body['isEvaluation'] = 0
            body['create_date'] = now
            body['tag'] = ",".join(tags)

            # user
            body['idRegister'] = user.id
            body['nickName'] = user.nickname
            body['birthYear'] = user.birth_year
            body['skinType'] = user._skin_type
            body['gender'] = user._gender
            body['registerScore'] = user.score
            body['registerRank'] = user.rank
            body['isBlind'] = user.is_blinded
            body['registerFileDir'] = user.file_dir
            body['registerFileSaveName'] = user.file_name_save

            # product
            body['idProduct'] = product.id
            body['productTitle'] = product.name
            body['idBrand'] = product.brand_id
            body['productFileDir'] = product.file_dir
            body['productFileSaveName'] = product.file_name
            body['brandTitle'] = product.brand.name
            body['productIsDisplay'] = int(product.is_display)

            categories = product.categories.all().values('id', 'main_category_id')
            body['firstCategoryList'] = ""
            body['secondCategoryList'] = ""
            for category in categories:
                body['firstCategoryList'] += "[" + str(category['main_category_id']) + "]"
                body['secondCategoryList'] += "[" + str(category['id']) + "]"

            try:
                goods_info = ProductGoods.objects.get(product_id=product_id, goods_count__gt=0)
                body['goods_info'] = {
                    "goods_count": goods_info.goods_count,
                    "min_price": goods_info.min_price,
                    "max_price": goods_info.max_price
                }
            except ProductGoods.DoesNotExist:
                pass

            elasticsearch_reviews.add(body=body, _id=review.id)
            
            is_first = not Review.objects.filter(product=product_id).exists()
            
        response = dict()
        response['review_count'] = user.review_set.count()

        # redis 에 update 하는 쿼리
        # 첫 번째 리뷰인지 확인한다.
        
        
        # 첫 리뷰시에 첫 리뷰 관리 테이블에 넣는다.
        if (is_first):
            try:
                Review_first_log(id=product_id, user=user,
                             timestamp=kst_now().strftime("%Y%m%d%H%M%S")
                             ).save(force_insert=True)
            except IntegrityError :
                # 테이블에 접근하는 순간 이미 product 가 존재해서 에러를 띄운다면 처음이 아님으로 is_first 를 False 로 변경한다.
                is_first = False
                
        review_create_cash = {
            'is_first':is_first,
            'written':True
        }
        # review count 에서 사용할 수 있도록 redis 에 set 해준다.
        set_review_is_written(user.id,review_create_cash)
        
        return Response(ReviewWriteResponse(response).data,
                        status=status.HTTP_201_CREATED)
    
    def update(self, request, pk=None):
        """
        리뷰 수정
        ---

        <br>
        <b>헤더</b>
        - IDREGISTER:        (필수) 회원 항번 <br>
        """

        # parameters
        cuid = int(request.META.get('HTTP_IDREGISTER') or 0)
        user = get_object_or_404(User, id=cuid)

        params = ReviewUpdateForm(data=request.data)
        params.is_valid(raise_exception=True)

        client_ip = get_client_ip(request)

        contents = params.validated_data.get('contents')
        new_rating = params.validated_data.get('rating')

        review = get_object_or_404(Review, id=pk, user=user, is_display=True)
        product = review.product

        with transaction.atomic():
            # review update
            # 블라인드 상태인 리뷰는 사용자가 수정시 검수중 상태로 변경된다.
            if review.state == 'B':
                review.state = 'C'

            review.ip_address = client_ip
            if contents:
                review.contents = contents
            if new_rating:
                review.rating = new_rating
            review.save()

            # product info update
            update_product_info.delay(product.id)

            # tag update
            tags = extract_tags(contents)
            now = local_now().strftime('%Y%m%d%H%M%S')

            object_tags = TagObject.objects.filter(type='review', object_id=review.id)
            # tag count update
            for _obj in object_tags:
                _obj.tag.count -= 1
                _obj.tag.modified_date = now
                _obj.tag.save()
            # delete tag mapping
            if object_tags.exists():
                object_tags.delete()

            for tag_name in tags:
                tag, created = Tag.objects.get_or_create(name=tag_name)
                if created:
                    TagObject(type='review', object_id=review.id, tag=tag).save()
                    tag.create_date = now
                    tag.save()
                else:
                    if not TagObject.objects.filter(type='review', object_id=review.id, tag=tag).exists():
                        TagObject(type='review', object_id=review.id, tag=tag).save()
                        tag.count += 1
                        tag.modified_date = now
                        tag.save()

            review.tag = ",".join(tags)

            # review update
            review.save()

            # elastic update
            body = {
                "doc": {'rating': new_rating,
                        'reviewText': contents,
                        'tag': ",".join(tags)}
            }
            elasticsearch_reviews.update(_id=review.id, body=body)

        return Response({}, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        """
        리뷰 삭제
        ---

        <br>
        <b>헤더</b>
        - IDREGISTER:        (필수) 회원 항번 <br>
        """
        cuid = int(request.META.get('HTTP_IDREGISTER') or 0)
        user = get_object_or_404(User, id=cuid)

        try:
            review_service.reset_rank(cuid)
            
            review = get_object_or_404(Review, id=pk, user=user,
                                       is_display=True)
            product = review.product
            
            with transaction.atomic():
                # 해당 리뷰에 블라인드 사유 삭제
                BlindedReview.objects.filter(review_id=pk).delete()
            
                # 좋아요 삭제
                Reviewlike.objects.filter(writer=user, product=product).delete()
            
                # 좋아요 알림 메세지 삭제
                MessageBox.objects.filter(
                    user=user, category=MessageCategory.objects.get(name='좋아요'), reference_id=review.id
                ).update(is_active=False)
            
                # review delete
                review.delete()
            
                # user info update
                user.review_count -= 1
                user.score -= 1
                user.save()
            
                # product info update
                update_product_info.delay(product.id)
            
                # tag update
                object_tags = TagObject.objects.filter(type='review', object_id=pk)
                now = local_now().strftime('%Y%m%d%H%M%S')
                # tag count update
                for _obj in object_tags:
                    _obj.tag.count -= 1
                    _obj.tag.modified_date = now
                    _obj.tag.save()
                # delete tag mapping
                if object_tags.exists():
                    object_tags.delete()
            
                # elastic delete
                elasticsearch_reviews.delete(_id=pk)
            
                # 레디스와 연동하기
                # 처음 리뷰 찾기
                first_review = Review_first_log.objects.filter(
                        id=product.id, user=user).all()[:1]
                
                is_first = len(first_review) > 0
                # 리뷰 포인트 가져오기
                review_points = review_service.get_review_points()
                user_review_count = review_service.get_review_count(user.id)
                this_week_user_review_count = \
                    review_service.get_this_week_review_count(user.id)
                
                score = review_points['review_point'] + \
                        ((user_review_count % 3 == 0) * \
                         review_points['multiple_bonus_point']) + \
                        (is_first * review_points['first_bonus_point'])
            
                
            
                # 처음 기존 리뷰 삭제
                if is_first is True:
                    first_review[0].delete()
            
                    # 처음 리뷰 검색후 넣어주기
                    new_first_reviews = Review.objects.filter(
                        product=product).order_by('_created_at').all()[:2]
            
                    # 최초 하나는 내 리뷰임으로 두번째 것을 넣어준다.
                    if len(new_first_reviews) > 1:
                        # 넣어준다
                        Review_first_log(
                            id=product.id, user=new_first_reviews[1].user,
                            timestamp=new_first_reviews[1]._created_at).save()
            
                        
            # 레디스는 automic 이 적용되지 않음으로 rdb 에서 동작을 마무리한 후 redis 에
            # 적용한다.
            # 삭제로 리뷰가 0개가 되는 순간 배치에서 감지하지 않음으로 주의해야 한다.

            # 레디스에 스코어 값 감소시키기
            # 리뷰가 정상이면
            if review.state == "N" and review.when_seceded == 0 and review.is_display == True and review.user.is_active == 1 and review.user.is_blinded == 0 and review.user.is_black == 0  :
                # 리뷰가 마지막이었다면
                if user_review_count == 1:
                    # rank 에서 삭제
                    period_zrem('all', user.id)
                else:
                    # 아니면 감소
                    period_zincrby('all', user.id, -score)
                
                # review 에 _created_at 은 kst 가 기준이기 떄문에 kst 로 비교한다
                if iso8601(datetime.strptime(
                        review._created_at, "%Y%m%d%H%M%S")) > \
                        iso8601(kst_last_week_friday_18_00()):
                    # 이번주 리뷰가 마지막이었다면
                    if  this_week_user_review_count == 1:
                        # 삭제한다
                        period_zrem('this_week', user.id)
                    else:
                        # 아니면 감소
                        period_zincrby('this_week', user.id, -score)
                # 처음 리뷰가 맞고 다른 사람이 쓴 것이 있으면
                if is_first is True and len(new_first_reviews) > 1:
                    # 처음 리뷰로 등록된 유저 보너스 점수 레디스에 등록하기
                    period_zincrby('all', new_first_reviews[1].user.id,
                                   review_points['first_bonus_point'])
                    if review._created_at > \
                            iso8601(kst_last_week_friday_18_00()):
                        period_zincrby('this_week',
                                   new_first_reviews[1].user.id,
                                   review_points['first_bonus_point'])
        except:
            raise

        
        
        return Response({}, status=status.HTTP_200_OK)

    @list_route(methods=['get'])
    def check(self, request):
        """
        리뷰 작성 확인
        ---
        헤더 값 <br>
        IDREGISTER (필수)
        """
        cuid = int(request.META.get('HTTP_IDREGISTER') or 0)
        if not cuid > 0:
            raise InvalidParameterException(
                _("로그인이 필요합니다.")
            )

        params = ReviewCheckForm(data=request.GET)
        params.is_valid(raise_exception=True)

        product_id = params.validated_data.get('product_id')

        response = dict()

        product = get_object_or_404(Product, id=product_id)
        response['product'] = product

        try:
            review = Review.objects.get(user_id=cuid, product=product)
            blinded_causes = blinded_review_service.get(review.id)
            setattr(review, 'blinded_causes',
                    [OrderedDict(
                        {'cause': item.cause.cause,
                         'guide': item.cause.guide}) for item in blinded_causes])

            response['is_comment'] = True
            response['review'] = review
            response['message'] = _("이미 리뷰를 작성한 제품입니다.\n수정하시겠어요?")

        except Review.DoesNotExist:
            response['is_comment'] = False

        return Response(ReivewCheckResponse(response).data, status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def like(self, request, pk=None):
        """
        리뷰 좋아요
        ---
        헤더 값 <br>
        IDREGISTER (필수)
        """
        from django.utils import timezone
        from libs.utils import utc_now

        cuid = int(request.META.get('HTTP_IDREGISTER') or 0)
        try:
            register = User.objects.get(id=cuid, is_active=True)
        except:
            raise InvalidParameterException(
                _("로그인이 필요합니다.")
            )

        review = get_object_or_404(Review, id=pk)
        product = review.product
        writer = review.user

        response = dict()

        if register.id == writer.id:
            raise ConflictException(
                _("나의 리뷰에는 좋아요 하실 수 없습니다.")
            )

        if Reviewlike.objects.filter(writer=writer, product=product, register=cuid).exists():
            raise ConflictException(
                _("이미 좋아요 하셨습니다.")
            )

        created_at = utc_now()
        create_date = format_round_datetime(created_at.astimezone(tz=timezone.get_current_timezone()))
        with transaction.atomic():
            # add one
            Reviewlike(
                writer=writer,
                product=product,
                register=register,
                create_date=create_date
            ).save()

            # writer info update
            user_updated_info = users_service.get_user_score_info(writer.id)
            writer.review_count = user_updated_info.get('review_count')
            writer.like_count = user_updated_info.get('like_count')
            writer.score = user_updated_info.get('score')
            writer.save()

            # review like count update
            review.like_count = Reviewlike.objects.using('default').filter(writer=writer, product=product).count()
            review.save()

            # elastic update
            body = {
                "doc": {'likeCount': review.like_count}
            }
            elasticsearch_reviews.update(_id=review.id, body=body)

        # 알림함
        try:
            review_service.make_like_message(review.id, register.id, created_at)
        except:
            pass

        # send push message
        push_text = "{} 님이 내 리뷰를 좋아합니다.\n{} - {}".format(
            register.nickname, product.brand.name, product.name
        )
        try:
            send_push_message(
                push_text,
                link_type=17,
                link_code=product.id,
                target_id=writer.id,
            )
        except:
            pass

        response['is_success'] = True
        response['message'] = _("좋아요 되었습니다.")

        return Response(SuccessMessageResponse(response).data, status=status.HTTP_201_CREATED)

    @detail_route(methods=['post'])
    def reports(self, request, pk=None):
        """
        리뷰 신고
        ---
        헤더 값 <br>
        IDREGISTER (필수)
        """
        cuid = int(request.META.get('HTTP_IDREGISTER') or 0)

        params = ReviewReportForm(data=request.data)
        params.is_valid(raise_exception=True)

        client_ip = get_client_ip(request)

        report_type = params.validated_data.get('report_type')
        contents = params.validated_data.get('contents')

        review = get_object_or_404(Review, id=pk)

        if cuid == review.user_id:
            raise InvalidParameterException()

        if review_service.has_report(pk, cuid):
            raise ConflictException(
                _("이미 신고한 리뷰입니다.")
            )

        review_service.create_report(pk, cuid, client_ip, report_type, contents, review.user_id)

        # 리뷰 신고 카운트 증가
        review.report_count += 1
        review.save()

        return Response({}, status=status.HTTP_201_CREATED)

    @detail_route(methods=['get'], url_path='can-report')
    def can_report(self, request, pk=None):
        """
        리뷰 신고 확인
        ---
        헤더 값 <br>
        IDREGISTER (필수)
        """
        cuid = int(request.META.get('HTTP_IDREGISTER') or 0)

        review = get_object_or_404(Review, id=pk)

        if cuid == review.user_id:
            raise InvalidParameterException()

        if review_service.has_report(pk, cuid):
            raise ConflictException(
                _("이미 신고한 리뷰입니다.")
            )

        return Response({}, status=status.HTTP_200_OK)

    @list_route(methods=['get'])
    def report_types(self, request):
        """
        리뷰 신고 유형 목록
        ---
        """
        type = 'review_report_type_cd'
        common_code = get_object_or_404(CommonCode, code_value=type)
        return Response(
            ReportTypesResponse({"report_types": review_service.get_report_types(common_code)}).data,
            status=status.HTTP_200_OK
        )

    @list_route(methods=['get'])
    def check_updated_rank_range(self, request):
        """
        리뷰 상승폭 확인
        ---
        헤더 값 <br>
        IDREGISTER (필수)
        """
        cuid = int(request.META.get('HTTP_IDREGISTER') or 0)
        if not cuid > 0:
            raise InvalidParameterException(
                _("로그인이 필요합니다.")
            )
        
        review_is_written = get_review_is_written(cuid)
        
        response = dict()
        response['user'] = User.objects.get(id=cuid)
        
        if review_is_written:
            review_count_all = review_service.get_review_count(cuid)
            # 리워드를 위한 계산
            is_multiple_all = review_count_all % 3 == 0
            # 처음 작성하는 리뷰라면 유저정보를 cache 에 올려준다.
            if review_count_all == 1:
                _user = User.objects.get(id=cuid)
                user_info = dict()
                user_info['idRegister'] = _user.id
                user_info['nickname'] = _user.nickname
                user_info['fileDir'] = _user.file_dir
                user_info['fileSaveName'] = _user.file_name_save
                period_hset('all', _user.id, json.dumps(user_info))
                
            
            # 누적을 기준으로 보너스를 결정하기 때문에 this_week에도 is_multiple_all 을
            # 넣어준다.
            rank_all = review_service.update_rank_point('all',
                cuid, is_multiple_all, review_is_written['is_first'])
            rank_this_week = review_service.update_rank_point('this_week',
                cuid, is_multiple_all, review_is_written['is_first'])
            
            # reward 시
            rewards = review_service.get_rewards(
                is_multiple_all,review_is_written['is_first'])
            
            # 누적과 이번주 랭킹 중 높은 것을 출력
            if rank_all is not None and rank_this_week is not None:
                if rank_this_week['rank'] <= rank_all['rank']:
                    rank_all = None
                else:
                    rank_this_week = None
            
            response['all'] = rank_all
            response['this_week'] = rank_this_week
            response['rewards'] = rewards
            
        else:
            response['all'] = None
            response['this_week'] = None
            response['rewards'] = None
        
        return Response(ReivewCheckRankRangeResponse(response).data,
                        status=status.HTTP_200_OK)
    
router = routers.DefaultRouter(trailing_slash=False)
router.register(r'reviews', ReviewView, base_name='reviews')
