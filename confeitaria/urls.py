from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
<<<<<<< HEAD

    # Admin
    path('admin/', admin.site.urls),

    # Autenticação
    path(
        'accounts/login/',
        auth_views.LoginView.as_view(template_name='core/login.html'),
        name='login'
    ),

    path(
        'accounts/logout/',
        auth_views.LogoutView.as_view(next_page='login'),
        name='logout'
    ),

    # Sistema principal
    path('', include('core.urls')),

    # API REST
    path('api/', include('core.api_urls')),

]

# Servir arquivos MEDIA (fotos dos colaboradores)
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
=======
    path('admin/', admin.site.urls),
    path('accounts/login/',
         auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('accounts/logout/',
         auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
>>>>>>> c693f1a340c5583664699999a38e44306a3d4a6f
