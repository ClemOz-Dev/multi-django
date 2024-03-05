from global_api.serializers.mixins.drf_validator_serializer_mixin import DrfValidatorSerializerMixin
from rest_framework import serializers


class UserLoginValidation(DrfValidatorSerializerMixin, serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(style={"input_type": "password"})
