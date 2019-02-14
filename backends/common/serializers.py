from collections import OrderedDict

from rest_framework import serializers


class GlowpickSerializer(serializers.Serializer):
    def to_representation(self, instance):
        """
        Object instance -> Dict of primitive datatypes.
        """
        ret = OrderedDict()
        fields = self._readable_fields

        for field in fields:
            from rest_framework.fields import SkipField
            try:
                attribute = field.get_attribute(instance)
            except SkipField:
                continue

            # We skip `to_representation` for `None` values so that fields do
            # not have to explicitly deal with that case.
            #
            # For related fields with `use_pk_only_optimization` we need to
            # resolve the pk value.
            from rest_framework.relations import PKOnlyObject
            check_for_none = attribute.pk if isinstance(attribute, PKOnlyObject) else attribute
            if check_for_none is None:
                # ret[field.field_name] = None
                continue
            else:
                representation = field.to_representation(attribute)

                if representation is None:
                    # Do not serialize empty objects
                    continue
                ret[field.field_name] = representation

        return ret


