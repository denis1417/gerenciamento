from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/',
         auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('accounts/logout/',
         auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('', include('core.urls')),   
]

from confeitaria.views_fs_colaboradores import (
    fs_colaboradores_list,
    fs_colaboradores_create,
    fs_colaboradores_detail,
)

urlpatterns += [
     path('fs/colaboradores/', fs_colaboradores_list, name='fs_colaboradores_list'),
     path('fs/colaboradores/novo/', fs_colaboradores_create, name='fs_colaboradores_create'),
     path('fs/colaboradores/<str:doc_id>/', fs_colaboradores_detail, name='fs_colaboradores_detail'),
]

from confeitaria.views_fs_insumos import (
    fs_insumos_list, fs_insumos_create, fs_insumos_detail
)

urlpatterns += [
    path('fs/insumos/', fs_insumos_list, name='fs_insumos_list'),
    path('fs/insumos/novo/', fs_insumos_create, name='fs_insumos_create'),
    path('fs/insumos/<str:doc_id>/', fs_insumos_detail, name='fs_insumos_detail'),
]

from confeitaria.views_fs_produtos import (
    fs_produtos_list, fs_produtos_create, fs_produtos_detail
)

urlpatterns += [
    path('fs/produtos/', fs_produtos_list, name='fs_produtos_list'),
    path('fs/produtos/novo/', fs_produtos_create, name='fs_produtos_create'),
    path('fs/produtos/<str:doc_id>/', fs_produtos_detail, name='fs_produtos_detail'),
]

from confeitaria.views_fs_fichas import (
    fs_fichas_list, fs_fichas_create, fs_fichas_detail
)

urlpatterns += [
    path('fs/fichas/', fs_fichas_list, name='fs_fichas_list'),
    path('fs/fichas/novo/', fs_fichas_create, name='fs_fichas_create'),
    path('fs/fichas/<str:doc_id>/', fs_fichas_detail, name='fs_fichas_detail'),
]

from confeitaria.views_fs_saidas import (
    fs_saidas_list, fs_saidas_create, fs_saidas_detail
)

urlpatterns += [
    path('fs/saidas/', fs_saidas_list, name='fs_saidas_list'),
    path('fs/saidas/novo/', fs_saidas_create, name='fs_saidas_create'),
    path('fs/saidas/<str:doc_id>/', fs_saidas_detail, name='fs_saidas_detail'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
