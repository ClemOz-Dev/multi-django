from dataclasses import dataclass

from global_api.serializers.mixins.dataclass_mixin import DataclassMixin


@dataclass
class AuthTokens(DataclassMixin):
    access: str
    refresh: str
