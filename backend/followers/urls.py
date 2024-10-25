from . import views
from django.urls import path, include
from rest_framework import routers

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'', views.FollowerViewSet, basename='followers')

urlpatterns = [
    path('/<path:foreign_author_id>', views.FollowerViewSet.as_view({
        'get': 'get_single',
        'put': 'update',
        'delete': 'destroy'
    }), name='get-follower'),
    path('', include(router.urls)),
]