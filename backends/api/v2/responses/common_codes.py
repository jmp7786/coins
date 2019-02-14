from rest_framework import serializers
from models.db_common.common_codes import CommonCodes, CommonCodeValues


class CommonCodeValueSerializer(serializers.ModelSerializer):

    class Meta:
        model = CommonCodeValues
        fields = ('id', 'value_cd', 'value_nm', 'sort_order')


class CommonCodesSerializer(serializers.ModelSerializer):
    common_code_values = CommonCodeValueSerializer(many=True, read_only=True,
                                                   help_text='공통 코드 값',
                                                   source='commoncodevalues_set')

    class Meta:
        model = CommonCodes
        fields = ('id', 'common_cd_value', 'common_cd_name', 'common_code_values')

