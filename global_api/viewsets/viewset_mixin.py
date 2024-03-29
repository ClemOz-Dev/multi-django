from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.settings import api_settings


class ViewSetMixin(viewsets.ViewSet):
    serializers = {"default": None}
    # The style to use for queryset pagination.
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    def get_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        serializer_key = kwargs.pop("serializer_key", None)
        serializer_class = self.get_serializer_class(serializer_key)
        return serializer_class(*args, **kwargs)

    @property
    def paginator(self):
        """
        The paginator instance associated with the view, or `None`.
        """
        if not hasattr(self, "_paginator"):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    def paginate_queryset(self, queryset):
        """
        Return a single page of results, or `None` if pagination is disabled.
        """
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def get_paginated_response(self, data):
        """
        Return a paginated style `Response` object for the given output data.
        """
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)

    @classmethod
    def get_serializer_by_key(cls, key):
        """
        Args:
            key: serializer key

        Returns:
            Serializer
        """
        return cls.serializers.get(key, cls.serializers["default"])

    def get_serializer_class(self, serializer_key=None):
        """
        Return the class to use for the serializer.
        Defaults to using `self.serializer_class`.

        You may want to override this if you need to provide different
        serializations depending on the incoming request.

        (Eg. admins get full serialization, others get basic serialization)

        Returns:
            Serializer: Drf or Serpy
        """
        serializer_key = serializer_key if serializer_key else self.action  # noqa
        return self.get_serializer_by_key(serializer_key)

    def get_action(self):
        # noinspection PyUnresolvedReferences
        return self.action_map.get(self.request.method.lower())

    def get_response(self, data, **params) -> Response:
        """
        Get response from data.

        Automatically serialize data from action name or parameter serializer_key

        Args:
            data(mixed): data to return in response
            **params:
                - serializer_key: serializer to use (default: action name)
                - status_code: default is status.HTTP_200_OK

        Returns:
            Response
        """
        default = {
            "serializer_key": None,
            "status_code": status.HTTP_200_OK,
        }
        params = {**default, **params}
        serializer_class = self.get_serializer_class(params["serializer_key"])
        many = isinstance(data, list)
        serializer = serializer_class(data, many=many)

        return Response(serializer.data, status=params.get("status_code"))

    def get_post_response(self, data, **params) -> Response:
        """
        Get post response from data.

        Automatically serialize data from action name or parameter serializer_key

        Args:
            data(mixed): data to return in response
            **params:
                - serializer_key: serializer to use (default: action name)
                - status_code: default is status.HTTP_201_CREATED
        Returns:
            Response
        """
        default = {
            "serializer_key": None,
            "status_code": status.HTTP_201_CREATED,
        }
        params = {**default, **params}
        return self.get_response(data, **params)

    # def get_validated_data(self, serializer_key=None, serializer_args=None):
    def get_validated_data(self, **kwargs):
        """
        Validate request data (throw exception if invalid) and return validated data.

        Args:
            kwargs: supported values are :
                    - serializer_key(None|str): serializer to use,
                        if not provided default is "<action name>_validation"
                    - context(None|dict): to pass context to serializer
                        (in the methods of the serializer, the context can be accessed
                         with statement "self.context")
                    - many(bool): True for list usage, False by default
        Returns:
            dict
        """
        serializer_key = kwargs.pop("serializer_key", None)
        if serializer_key is None:
            serializer_key = f"{self.action}_validation"
        if serializer_key not in self.serializers:
            raise RuntimeError(f"You need to define '{serializer_key}' serializer")
        serializer_class = self.get_serializer_class(serializer_key)
        serializer = serializer_class(data=self.request.data, **kwargs)
        if self.request.query_params and not self.request.data:
            serializer = serializer_class(data=self.request.query_params, **kwargs)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    @classmethod
    def simplify_errors(cls, errors):
        if isinstance(errors, dict):
            return {attr: cls.simplify_errors(errs) for attr, errs in errors.items()}
        if isinstance(errors, list) and isinstance(errors[0], dict):
            # Simplify many to many relations errors
            many2many_errors = []
            for item_errors in errors:
                many2many_errors.append(cls.simplify_errors(item_errors))
            return many2many_errors
        return str(errors[0])

    @staticmethod
    def get_error_validation_response(error: ValidationError):
        """
        Build validation error response with status code of 422 and
        by keeping only first validation message
        """
        data = {}
        for attr, errors in error.detail.items():
            data[attr] = str(errors[0])
        return Response(data, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    def check_is_valid(self, **kwargs):
        """
        Validate request data (throw exception if invalid) and return validated data.

        Args:
            kwargs: supported values are :
                    - serializer_key(None|str) : serializer to use,
                        if not provided default is "<action name>_validation"
                    - context(None|dict) : to pass context to serializer
                        (in the methods of the serializer, the context can be accessed
                         with statement "self.context")
        Returns:
            dict
        """
        try:
            validated_data = self.get_validated_data(**kwargs)
        except ValidationError as e:
            errors = self.simplify_errors(e.detail)
            raise ValidationError(errors)
        return dict(validated_data)

    def check_is_list_valid(self, serializer_key=None):
        try:
            validated_data = self.get_validated_data(
                serializer_key=serializer_key, many=True
            )
        except ValidationError as e:
            errors = self.simplify_errors(e.detail)
            raise ValidationError(errors)
        return list(validated_data)

    @action(methods=["post"], detail=False)
    def validate(self, request):
        """
        Validate using query params action to retrieve serializer name

        POST <viewset>/validate/?action=<action name>
        """
        action_name = self.request.GET.get("action")
        if action_name is None:
            raise RuntimeError("missing query parameter 'action'")
        validated_data = self.check_is_valid(serializer_key=f"{action_name}_validation")
        return Response(validated_data)
