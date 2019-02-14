from rest_framework import serializers


class ReviewRating(serializers.Serializer):
    point_1 = serializers.IntegerField()
    point_2 = serializers.IntegerField()
    point_3 = serializers.IntegerField()
    point_4 = serializers.IntegerField()
    point_5 = serializers.IntegerField()


class Scoreboard(serializers.Serializer):
    blinded = serializers.IntegerField(required=False)
    ratings = ReviewRating(required=False)
