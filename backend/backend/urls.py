"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from django.urls.conf import include
import restapi.urls
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/health/", include("health_check.urls")),
    path("api/admin/", admin.site.urls),
    path('api/auth/', include('rest_framework.urls', namespace='rest_framework'))
]

# add the restapi urls
urlpatterns += restapi.urls.urlpatterns

urlpatterns += [
    # catch all other paths that *do not* start with /api
    # we can use index.html because settings.py/TEMPLATES/DIRS is set to the frontend build folder
    # https://stackoverflow.com/a/34706672
    re_path(r'^(?!api).*', TemplateView.as_view(template_name="index.html"))
]
