# market/urls.py  (your project-level urls, not core/urls.py)
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),

    # OpenAPI schema (machine readable)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI (interactive docs)
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # Optional ReDoc UI
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Your API app
    path('api/', include('core.urls')),
]
