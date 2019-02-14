from rest_framework import serializers
from models.db_common.faqs import Faq
from django.utils import timezone
from models.db_common.common import SERVICE_TYPE_CDS


class FaqSerializer(serializers.ModelSerializer):

    service_type_cd = serializers.ChoiceField(required=True,
                                              choices=SERVICE_TYPE_CDS,
                                              help_text="서비스 타입 구분")
    board_detail_type_cd = serializers.ChoiceField(required=True,
                                                   choices=Faq.BOARD_DETAIL_TYPE_CDS,
                                                   help_text="게시판 상세 타입 구분")
    created_at = serializers.HiddenField(default=serializers.CreateOnlyDefault(timezone.now))
    updated_at = serializers.HiddenField(default=timezone.now)
    created_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Faq
        fields = ('id', 'service_type_cd', 'board_detail_type_cd', 'question', 'answer',
                  'is_best', 'created_at', 'updated_at', 'created_id')
        extra_kwargs = {
            'question': {'help_text': '제목'},
            'answer': {'help_text': '내용'},
            'is_best': {'help_text': 'Best 여부'},
        }
