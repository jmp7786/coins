from rest_framework import serializers


class NoticeSerializer(serializers.Serializer):
    notice_id = serializers.IntegerField(source='id')
    board_type_code = serializers.CharField(source='board_type_cd', max_length=50)
    board_category_code = serializers.CharField(source='board_category_cd', max_length=50)
    subject = serializers.CharField(max_length=255)
    content = serializers.CharField(max_length=None)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    def to_representation(self, instance):
        dict_category = self.context['dict_category']
        result = super(NoticeSerializer, self).to_representation(instance)
        result['board_category_name'] = dict_category[result['board_category_code']] \
            if result['board_category_code'] in dict_category.keys() else None
        return result


class NoticeCategorySerializer(serializers.Serializer):
    category_code = serializers.CharField(source='value_cd', max_length=255)
    category_name = serializers.CharField(source='value_nm', max_length=255)


class Notice(serializers.Serializer):
    notice_id = serializers.IntegerField(source='id')
    title = serializers.CharField(source='subject')
    created_at = serializers.DateTimeField()
