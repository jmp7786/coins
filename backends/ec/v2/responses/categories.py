from rest_framework import serializers

from models.products import MainCategory, SubCategory


class MainCategoryBaseSerializer(serializers.ModelSerializer):
    main_category_id = serializers.IntegerField(source='id')

    class Meta:
        model = MainCategory
        fields = ('main_category_id', 'name')


class SubCategoryBaseSerializer(serializers.ModelSerializer):
    sub_category_id = serializers.IntegerField(source='id')

    class Meta:
        model = SubCategory
        fields = ('sub_category_id', 'name')


class ProductCategoryResponse(serializers.ModelSerializer):
    sub_category_id = serializers.IntegerField(source='id')
    main_category = MainCategoryBaseSerializer(
        required=False
    )

    class Meta:
        model = SubCategory
        fields = ('sub_category_id', 'name', 'main_category')
