from global_api.services.abstract_service import AbstractService
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

from global_api.services.models.auth_model import AuthTokens
from multi_exceptions import InvalidCredentialsError, _


class AuthService(AbstractService):
    @classmethod
    def login(
            cls,
            username: str,
            password: str,
    ) -> tuple[User, AuthTokens]:
        user = authenticate(username=username, password=password)

        if user is None:
            raise InvalidCredentialsError(
                _("Unable to log in with provided credentials.")
            )

        return user, cls.get_user_tokens(user)

    @classmethod
    def get_user_tokens(
            cls, user: User
    ) -> AuthTokens:
        return cls._get_tokens(user)

    @classmethod
    def _get_tokens(
            cls,
            user: User,
    ):
        refresh_token = RefreshToken.for_user(user)

        return AuthTokens(
            access=str(refresh_token.access_token),
            refresh=str(refresh_token),
        )
