from rest_framework import serializers

from models.db_common.common_codes import CommonCodeValues

BOARD_TYPE = {'service': '01', 'ec': '03'}


def validate_board_type(value):
    if value not in BOARD_TYPE.keys():
        raise serializers.ValidationError("This field is not valid.")


def validate_board_category(value):
    if not CommonCodeValues.objects.filter(common_codes__common_cd_value='board_category_cd', value_cd=value).exists():
        raise serializers.ValidationError("This field is not valid.")


class NoticesForm(serializers.Serializer):
    cursor = serializers.IntegerField(default=1)
    limit = serializers.IntegerField(default=20, required=False)
    board_type = serializers.CharField(default=None, validators=[validate_board_type])
    board_category = serializers.CharField(default=None, validators=[validate_board_category])

    def to_representation(self, obj):
        return {
            'cursor': obj['cursor'],
            'limit': obj['limit'],
            'board_type': BOARD_TYPE[obj['board_type']] if obj['board_type'] in BOARD_TYPE.keys() else None,
            'board_category': obj['board_category']
        }


class NoticeForm(serializers.Serializer):
    board_type = serializers.CharField(validators=[validate_board_type])

    def to_representation(self, obj):
        return {
            'board_type': BOARD_TYPE[obj['board_type']]
        }
