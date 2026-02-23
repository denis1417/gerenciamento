from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path('admin/', admin.site.urls),

    # URLs do seu app core
    path('', include('core.urls')),

    # API
    path('api/', include('core.api_urls')),

]

# suporte a arquivos media
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
