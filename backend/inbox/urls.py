from inbox import views
from django.urls import path, include
from rest_framework import routers

# Create a router and register the post, like, and comment viewsets with it
router = routers.DefaultRouter(trailing_slash=False)
router.register(r'', views.InboxViewSet, basename='inbox')

urlpatterns = [
    path('', include(router.urls)),
]