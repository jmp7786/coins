import datetime
import os

from django.conf import settings
from rest_framework import serializers

from libs.utils import local_now
from models.messages import MessageBox, MessageCategory, MessageCheck, MessageTarget
from models.products import Product
from models.push_messages import PushMessages
from models.requested_products import RequestedNewProduct, RequestedEditProduct, RequestedIngredient
from models.reviews import Review, Reviewlike


class MessageCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageCategory
        fields = '__all__'


class MessageSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = MessageBox
        fields = (
            'user_id', 'category', 'message', 'reference_id', 'created_at'
        )
        read_only_fields = [
            'id'
        ]

    def to_representation(self, instance):

        user_id = int(self.context['request'].META.get('HTTP_IDREGISTER') or 0)

        resposne = {
            'id': instance.id,
            'category': instance.category.name,
            'licon_image': instance.category.icon_image,
            'is_checked': MessageCheck.objects.filter(
                user_id=user_id, message=instance, read_at__isnull=False).exists(),
            'created_at': instance.created_at,
            'reference_id': instance.reference_id
        }

        for k, v in self.message_template(instance).items():
            resposne[k] = v

        return resposne

    def message_template(self, instance):
        code = instance.category.name
        if code == '알림':
            return self.make_push_message(instance)
        elif code == '제품등록':
            return self.make_requested_message(instance)
        elif code == '제품수정':
            return self.make_requested_message(instance)
        elif code == '성분등록':
            return self.make_requested_message(instance)
        elif code == '가입완료':
            return self.make_signup_messsage(instance)
        elif code == '좋아요':
            return self.make_like_message(instance)

    def make_push_message(self, instance):
        """
        알림 ( 전체 푸시 메세지 )
        """
        try:
            push_message = PushMessages.objects.get(id=instance.reference_id)

            types_no_use_code = [11, 24, 28, 33]

            target_url = "glowpick://glowpick.com?type={}&code={}".format(
                push_message.link_type, push_message.link_code.strip()
            )

            product = None
            if push_message.link_type == 17:  # 제품 상세 이동
                product = Product.objects.select_related('brand').get(id=push_message.link_code.strip())

            response = dict()
            if instance.message:
                response['message'] = instance.message
            if push_message.big_picture:
                response['big_picture_image'] = push_message.big_picture
            if product:
                response['ricon_image'] = product.product_image_160

            if push_message.link_type:
                if not (push_message.link_type not in types_no_use_code and not push_message.link_code):
                    response['target_url'] = target_url

            return response
        except (PushMessages.DoesNotExist, Product.DoesNotExist, ValueError):
            return {
                'messages': instance.message
            }

    def make_signup_messsage(self, instance):
        """
        가입완료
        """
        return {
            'message': instance.message,
            'target_url': "glowpick://glowpick.com?type=16&code=670"
        }

    def make_requested_message(self, instance):
        """
        제품등록, 제품수정, 성분등록 메세지 처리
        """
        try:
            target = MessageTarget.objects.get(message=instance)

            target_url = "glowpick://glowpick.com?type={}&code={}".format(target.link_type, target.link_code.strip())
            product = None
            if target.link_type == '17':  # 제품 상세 이동
                product = Product.objects.select_related('brand').get(id=target.link_code.strip())

            response = dict()
            if instance.message:
                response['message'] = instance.message
            if product:
                response['ricon_image'] = product.product_image_160

            types_no_use_code = ['11', '24', '28', '33']
            if not (target.link_type not in types_no_use_code and not target.link_code):
                response['target_url'] = target_url

            return response

        except (MessageTarget.DoesNotExist, Product.DoesNotExist, ValueError):
            return {
                'message': instance.message
            }

    def make_like_message(self, instance):
        """
        좋아요
        """
        try:
            from django.utils import timezone
            review = Review.objects.select_related(
                'user', 'product', 'product__brand'
            ).get(
                id=instance.reference_id
            )

            two_week_ago = local_now() - datetime.timedelta(days=14)

            likes = Reviewlike.objects.select_related('register').filter(
                writer=review.user, product=review.product,
                create_date__gte=two_week_ago.strftime('%Y%m%d%H%M%S'),
            )
            likes = likes.filter(
                create_date__gte=instance.created_at.astimezone(
                    tz=timezone.get_current_timezone()
                ).strftime('%Y%m%d%H%M%S')
            )

            likes = likes.values(
                # 'register__nickname',
                'register__file_name_save',
                'register__file_dir'
            )
            first = list(likes)[-1]

            icon_image = "{}{}/{}".format(
                settings.CDN, first.get('register__file_dir'), first.get('register__file_name_save')
            )
            path = os.path.splitext(icon_image)
            thumbnail = '%s_160%s' % (path[0], path[1])

            return {
                'message': instance.message,
                'licon_image': thumbnail,
                'ricon_image': review.product.product_image_160,
                'target_url': "glowpick://glowpick.com?type=17&code={}".format(review.product_id),
                'created_at': instance.updated_at if instance.updated_at else instance.created_at
            }
        except (Review.DoesNotExist, IndexError):
            return {
                'message': instance.message
            }

    def to_internal_value(self, data):

        # Perform the data validation.
        category = data.get('category')

        if not category:
            raise serializers.ValidationError({
                'category': 'This field is required.'
            })

        try:
            if hasattr(data, '_mutable'):
                data._mutable = True
            data['category'] = MessageCategory.objects.get(name=data.get('category'))
        except MessageCategory.DoesNotExist as err:
            raise serializers.ValidationError({
                'category': str(err)
            })

        return data


class MessageReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageCheck
        fields = '__all__'
        read_only_fields = ('user_id', 'checked_at', 'read_at')


class MessageTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageTarget
        fields = '__all__'
