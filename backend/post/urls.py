from post import views
from django.urls import path, include
from rest_framework import routers

# Create a router and register the post, like, and comment viewsets with it
router = routers.DefaultRouter(trailing_slash=False)
router.register(r'(?P<post_id>[^/.]+)/comments', views.CommentViewSet, basename='comment')
router.register(r'(?P<post_id>[^/.]+)/likes', views.LikeViewSet, basename='like')
router.register(r'(?P<post_id>[^/.]+)/comments/(?P<comment_id>[^/.]+)/likes', views.LikeViewSet, basename='like')
# router.register(r'(?P<post_id>[^/.]+)/image/', views.ImagePostViewSet, basename='image')

urlpatterns = [
    path('/public', views.PostViewSet.as_view({'get': 'public_posts'}), name='public-posts'),
    path('/following', views.PostViewSet.as_view({'get': 'retrive_friends_follwing'}), name='retrive-friends-follwing'),
    path('', views.PostViewSet.as_view({'get': 'list', 'post': 'create'}), name='retrive-posts'),
    path('/<str:pk>', views.PostViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='retrive-post'),
    path('/', include(router.urls)),
    path('/<str:post_id>/image', views.PostViewSet.as_view({'get': 'retrive_image'}), name='retrive-image')
]