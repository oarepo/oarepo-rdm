import marshmallow as ma
from flask_resources import MarshmallowSerializer, JSONSerializer, BaseListSchema


class ModelSchema(ma.Schema):
    title = ma.fields.String()

    class Meta:
        unknown = ma.INCLUDE


class ModelUISerializer(MarshmallowSerializer):
    """UI JSON serializer."""

    def __init__(self):
        """Initialise Serializer."""
        super().__init__(
            format_serializer_cls=JSONSerializer,
            object_schema_cls=ModelSchema,
            list_schema_cls=BaseListSchema,
            schema_context={"object_key": "ui"},
        )
