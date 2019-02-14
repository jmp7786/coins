from rest_framework.validators import UniqueValidator, qs_exists

from backends.common.exceptions import InvalidParameterException


class CustomUniqueValidator(UniqueValidator):
    def __call__(self, value):
        queryset = self.queryset
        queryset = self.filter_queryset(value, queryset)
        queryset = self.exclude_current_instance(queryset)
        if qs_exists(queryset):
            raise InvalidParameterException(self.message, code='unique')
