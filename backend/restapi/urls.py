from . import views
from rest_framework import routers
from django.urls import path, include
from post import urls as post_urls
from inbox import urls as inbox_urls
from followers import urls as followers_urls

# Create a router and register the user and author viewsets with it
router = routers.DefaultRouter(trailing_slash=False)
router.register('users', views.UserViewSet, basename='user')
router.register('authors', views.AuthorViewSet, basename='author')

# nested viewset
# https://browniebroke.com/blog/nested-viewsets-with-django-rest-framework/
# router.register("authors/(?P<author_id>[^/.]+)/posts", views.PostViewSet, basename='post')
# router.register(r'likes', views.LikeViewSet)
# router.register(r'comments', views.CommentViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/auth', views.AuthView.as_view()),
    path('api/authors/all', views.AuthorViewSet.as_view({ 'get': 'list' })),
    path('api/authors/<str:author_id>/posts', include(post_urls)),
    path('api/authors/<str:author_id>/inbox', include(inbox_urls)),
    path('api/authors/<str:author_id>/liked', views.LikedViewSet.as_view({'get': 'list'})),
    path('api/authors/<str:author_id>/followers', include(followers_urls)),
    path('api/update_github', views.UpdateGithub.as_view())
]