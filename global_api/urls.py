from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from global_api.quickstart import views
from global_api.viewsets.auth_viewset import AuthViewSet

router = routers.SimpleRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r"auth", AuthViewSet, basename="auth")


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]

urlpatterns += router.urls
