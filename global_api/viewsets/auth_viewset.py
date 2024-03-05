from django.contrib.auth import login
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import viewsets

from global_api.serializers import drf_serializers
from global_api.services.technical.auth_service import AuthService
from global_api.viewsets.viewset_mixin import ViewSetMixin


class AuthViewSet(ViewSetMixin):
    serializers = {
        "default": None,
        "login_validation": drf_serializers.UserLoginValidation,
    }

    @action(methods=["post"], detail=False, permission_classes=[AllowAny])
    def login(self, request, **kwargs):
        validated_data = self.check_is_valid(context={"request": request})
        user, auth_tokens = AuthService.login(**validated_data)
        login(request, user)
        return Response(data=auth_tokens.to_dict())
