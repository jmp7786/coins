from rest_framework import serializers
from models.db_common.inquiries import Inquiry, InquiryReply
from django.utils import timezone
from models.db_common.common import SERVICE_TYPE_CDS


class InquiryReplySerializer(serializers.ModelSerializer):

    name = serializers.CharField(help_text="답변자")
    content = serializers.CharField(help_text="답변내용")
    created_at = serializers.DateTimeField(help_text="답변 등록일")
    updated_at = serializers.DateTimeField(help_text="답변 수정일")

    class Meta:
        model = InquiryReply
        fields = ('name', 'content', 'updated_at', 'created_at')


def check_attr(data, attr_name):
    error_detail = []
    try:
        if not data[attr_name]:
            error_detail.append("This field may not be null.")
    except KeyError:
        error_detail.append("This field is required.")
    return error_detail


class InquirySerializer(serializers.ModelSerializer):

    inquiry_reply = InquiryReplySerializer(many=True, read_only=True,
                                           help_text="문의 답변", source='inquiryreply_set')
    name = serializers.CharField(required=True, help_text="이름")
    email = serializers.EmailField(required=True, help_text="이메일주소")
    is_email = serializers.BooleanField(default=False, help_text="이메일로 답변 받기")
    is_sms = serializers.BooleanField(default=False, help_text="SMS로 답변 받기")
    contact = serializers.CharField(required=True, help_text="휴대전화")
    content = serializers.CharField(required=True, help_text="문의내용")
    customer_id = serializers.IntegerField(required=False, help_text="고객 ID")
    company_name = serializers.CharField(required=False, help_text="브랜드명/업체명")

    service_type_cd = serializers.ChoiceField(required=True,
                                              choices=SERVICE_TYPE_CDS,
                                              help_text="서비스 타입 구분")
    board_type_cd = serializers.ChoiceField(required=True,
                                            choices=Inquiry.BOARD_TYPE_CDS,
                                            help_text="게시판 구분")
    board_detail_type_cd = serializers.ChoiceField(required=True,
                                                   choices=Inquiry.BOARD_DETAIL_TYPE_CDS,
                                                   help_text="게시판 상세 타입 구분")

    product_id = serializers.IntegerField(required=False, help_text="상품 ID")
    product_code = serializers.CharField(required=False, help_text="상품 코드")
    product_name = serializers.CharField(required=False, help_text="상품 이름")
    product_image_url = serializers.URLField(required=False, help_text="상품 이미지")
    created_at = serializers.DateTimeField(read_only=True,
                                           default=serializers.CreateOnlyDefault(timezone.now))
    updated_at = serializers.DateTimeField(read_only=True, default=timezone.now)
    is_del = serializers.HiddenField(help_text="삭제 여부", default=False)
    is_answered = serializers.BooleanField(read_only=True, help_text="답변 여부", default=False)

    service_board_type_mapping = {
        'SV': {
           'BT03': (
               'BT03_01',
               'BT03_02',
               'BT03_03',
               'BT03_04',
               'BT03_05',
                    ),
        },
        'EC': {
            'BT03': (
                'BT03_06',
                'BT03_07',
                'BT03_08',
                'BT03_09',
            ),
            'BT04': (
                'BT04_01',
            )
        }
    }

    def validate(self, attrs):

        customer_id = attrs.get('customer_id')
        if customer_id:
            attrs['created_id'] = customer_id
            attrs['updated_id'] = customer_id
        service_type_cd = attrs['service_type_cd']
        board_type_cd = attrs['board_type_cd']
        board_detail_type_cd = attrs['board_detail_type_cd']

        try:
            if board_detail_type_cd not in \
                    self.service_board_type_mapping[service_type_cd][board_type_cd]:
                raise serializers.ValidationError('board_detail_type_cd:{board_detail_type_cd} '
                                                  'board_type_cd:{board_type_cd} mapping 되지 않음'.format(
                                                    board_detail_type_cd=board_detail_type_cd,
                                                    board_type_cd=board_type_cd), code=0)
        except KeyError:
            raise serializers.ValidationError('service_type_cd:{service_type_cd} '
                                              'board_type_cd:{board_type_cd} mapping 되지 않음'.format(
                                                service_type_cd=service_type_cd,
                                                board_type_cd=board_type_cd))
        error_detail = {}
        required_attrs = []

        if board_type_cd == 'BT04':
            required_attrs = ('product_id', 'product_name', 'product_code', 'product_image_url')

        if board_detail_type_cd == 'BT03_04':
            required_attrs = ['company_name']

        for attrs_name in required_attrs:
            attrs_error_detail = check_attr(attrs, attrs_name)
            if attrs_error_detail:
                error_detail.setdefault(attrs_name, []).extend(attrs_error_detail)

        if error_detail:
            raise serializers.ValidationError(error_detail)
        return attrs

    class Meta:
        model = Inquiry
        fields = ('id', 'service_type_cd',  'board_type_cd', 'board_detail_type_cd',
                  'customer_id', 'name', 'contact', 'email', 'content', 'environment_info',
                  'inquiry_reply', 'product_id', 'product_code', 'product_name', 'product_image_url',
                  'is_email', 'is_sms', 'created_at', 'updated_at', 'company_name', 'is_answered',
                  'is_del', 'nickname'
                  )

        read_only_fields = ('id', 'is_answered')
