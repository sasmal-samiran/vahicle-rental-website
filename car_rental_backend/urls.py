from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('django-admin/', admin.site.urls),
    
    # REST API endpoints
    path('api/', include('apps.users.urls')),
    path('api/', include('apps.vehicles.urls')),
    path('api/', include('apps.bookings.urls')),
    path('api/', include('apps.payments.urls')),
    path('api/', include('apps.reviews.urls')),
    path('api/', include('apps.notifications.urls')),
    path('api/', include('apps.analytics.urls')),

    # # OpenAPI / Swagger Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Frontend Single Page / Multi View Routes
    path('', TemplateView.as_view(template_name='base.html'), name='customer-home'),
    path('fleet/', TemplateView.as_view(template_name='fleet.html'), name='fleet-catalog'),
    path('admin-portal/', TemplateView.as_view(template_name='admin.html'), name='admin-portal'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
