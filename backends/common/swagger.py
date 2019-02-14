from rest_framework import exceptions
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.renderers import CoreJSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_swagger import renderers
from django.utils.encoding import force_text

from rest_framework.schemas import SchemaGenerator
from rest_framework.metadata import SimpleMetadata
from rest_framework.compat import (
    coreapi
)

from openapi_codec import encode


def _custom_get_responses(link):
    return link._responses_docs


# Very nasty; Monkey patching;
encode._get_responses = _custom_get_responses


class CustomSchemaGenerator(SchemaGenerator):
    def get_link(self, path, method, view):
        link = super(CustomSchemaGenerator, self).get_link(path, method, view)

        # Custom parameter
        link._fields += self.get_core_fields(method, view)

        # Custom response
        link._responses_docs = self.get_response_docs(method, view)

        return link

    def get_serializer_fields(self, path, method, view):
        fields = super(CustomSchemaGenerator, self).get_serializer_fields(path, method, view)

        return fields

    def get_core_fields(self, method, view):
        serializer_classes = getattr(view, 'parameter_classes', None)

        fields = ()

        if serializer_classes:
            if hasattr(view, 'action'):
                serializer_class = serializer_classes.get('{}_{}'.format(method.lower(), view.action))
            else:
                serializer_class = serializer_classes.get(method.lower())
            if serializer_class:
                _s = serializer_class(context={'request': view.request, 'view': view})
                for field in _s.fields.values():
                    if field.read_only or isinstance(field, serializers.HiddenField):
                        continue

                    required = field.required
                    description = force_text(field.help_text) if field.help_text else ''
                    field = coreapi.Field(
                        name=field.field_name,
                        location='form' if method != 'GET' else 'query',
                        required=required,
                        description=description,
                        type=SimpleMetadata.label_lookup[field]
                    )
                    fields += (field,)

        return fields

    def get_response_docs(self, method, view):

        template = {'description': 'No response docs definition found.'}
        if method.lower() == 'post':
            default_response_docs = {'201': template}
        elif method.lower() == 'delete':
            default_response_docs = {'204': template}
        else:
            default_response_docs = {'200': template}

        response_docs = view.response_docs if hasattr(view, 'response_docs') else default_response_docs

        if hasattr(view, 'action'):
            docs = response_docs.get('{}_{}'.format(method.lower(), view.action), default_response_docs)
        else:
            docs = response_docs.get('{}'.format(method.lower()), default_response_docs)

        if docs:
            for status_code in docs.keys():
                schema = docs[status_code].get('schema')
                if schema and isinstance(schema, dict):
                    type = schema.get('type')
                    if type == 'array':
                        items = schema.get('items')
                        if items and isinstance(items, dict):
                            serializer_class = items.get('properties')
                            if serializer_class and not isinstance(serializer_class, dict):
                                _s = serializer_class(context={'request': view.request, 'view': view})
                                properties = self._get_properties(_s)
                                docs[status_code]['schema']['items']['properties'] = properties
                    elif type == 'object':
                        serializer_class = schema.get('properties')
                        if serializer_class and not isinstance(serializer_class, dict):
                            _s = serializer_class(context={'request': view.request, 'view': view})
                            properties = self._get_properties(_s)
                            docs[status_code]['schema']['properties'] = properties

            response_docs = docs

        return response_docs

    def _get_properties(self, serializer):
        properties = {}
        for field in serializer.fields.values():
            if isinstance(field, serializers.HiddenField):
                continue
            properties[field.field_name] = {
                'type': SimpleMetadata.label_lookup[field]
                if SimpleMetadata.label_lookup[field] != 'nested object'
                else 'object',

                'description': force_text(field.help_text)
                if field.help_text
                else '',
            }
            if properties[field.field_name]['type'] == 'field':
                if field._kwargs.get('child'):
                    properties[field.field_name]['type'] = 'array'
                    properties[field.field_name]['items'] = {}
                    properties[field.field_name]['items']['type'] = 'object'
                    properties[field.field_name]['items']['properties'] = self._get_properties(field.child)
            elif properties[field.field_name]['type'] == 'object':
                properties[field.field_name]['properties'] = self._get_properties(field)

        return properties


def get_swagger_view(title=None, url=None, patterns=None, urlconf=None):
    """
    Returns schema view which renders Custom Swagger/OpenAPI.
    """

    class SwaggerSchemaView(APIView):
        _ignore_model_permissions = True
        exclude_from_schema = True
        permission_classes = [AllowAny]
        renderer_classes = [
            CoreJSONRenderer,
            renderers.OpenAPIRenderer,
            renderers.SwaggerUIRenderer
        ]

        def get(self, request):
            generator = CustomSchemaGenerator(
                title=title,
                url=url,
                patterns=patterns,
                urlconf=urlconf
            )
            schema = generator.get_schema(request=request)

            if not schema:
                raise exceptions.ValidationError(
                    'The schema generator did not return a schema Document'
                )

            return Response(schema)

    return SwaggerSchemaView.as_view()
