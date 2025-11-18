"""
URL Configuration for MoFA FM
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# API Documentation
schema_view = get_schema_view(
    openapi.Info(
        title="MoFA FM API",
        default_version='v1',
        description="MoFA FM Podcast Platform API",
        contact=openapi.Contact(email="contact@mofa.ai"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # API Endpoints
    path('api/auth/', include('apps.users.urls')),
    path('api/podcasts/', include('apps.podcasts.urls')),
    path('api/interactions/', include('apps.interactions.urls')),
    path('api/search/', include('apps.search.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
