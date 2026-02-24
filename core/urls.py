from django.urls import path, include
from . import views

# API REST
from rest_framework.routers import DefaultRouter
from .views import ProdutoViewSet, InsumoViewSet, ColaboradorViewSet


# =========================================================
# ROTAS PRINCIPAIS
# =========================================================

urlpatterns = [

    # =====================================
    # LOGIN / LOGOUT
    # =====================================

    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # =====================================
    # HOME E DASHBOARD
    # =====================================

    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('relatorio/pdf/', views.relatorio_pdf, name='relatorio_pdf'),

    # =====================================
    # COLABORADORES
    # =====================================

    path('colaboradores/', views.colaboradores_list, name='colaboradores_list'),

    path('colaboradores/novo/',
         views.colaboradores_create,
         name='colaboradores_create'),

    path('colaboradores/<int:id>/',
         views.colaboradores_detail,
         name='colaboradores_detail'),

    path('colaboradores/<int:id>/editar/',
         views.colaboradores_edit,
         name='colaboradores_edit'),

    path('colaboradores/<int:id>/excluir/',
         views.colaboradores_delete,
         name='colaboradores_delete'),

    # =====================================
    # INSUMOS
    # =====================================

    path('insumos/',
         views.insumos_list,
         name='insumos_list'),

    path('insumos/novo/',
         views.insumos_create,
         name='insumos_create'),

    path('insumos/<int:id>/editar/',
         views.insumos_edit,
         name='insumos_edit'),

    path('insumos/<int:id>/deletar/',
         views.insumos_delete,
         name='insumos_delete'),

    # =====================================
    # PRODUTOS PRONTOS
    # =====================================

    path('produtos/',
         views.produtos_list,
         name='produtos_list'),

    path('produtos/novo/',
         views.produtos_create,
         name='produtos_create'),

    path('produtos/<int:id>/editar/',
         views.produtos_edit,
         name='produtos_edit'),

    path('produtos/<int:id>/deletar/',
         views.produtos_delete,
         name='produtos_delete'),

    # =====================================
    # CATÁLOGO
    # =====================================

    path('catalogo/',
         views.catalogo_list,
         name='catalogo_list'),

    path('catalogo/novo/',
         views.catalogo_create,
         name='catalogo_create'),

    path('catalogo/<int:pk>/editar/',
         views.catalogo_edit,
         name='catalogo_edit'),

    path('catalogo/<int:pk>/deletar/',
         views.catalogo_delete,
         name='catalogo_delete'),

    # =====================================
    # FICHAS DE PRODUÇÃO
    # =====================================

    path('produtos/ficha/criar/',
         views.criar_ficha,
         name='criar_ficha'),

    path('produtos/ficha/<int:ficha_id>/visualizar/',
         views.visualizar_ficha,
         name='visualizar_ficha'),

    # =====================================
    # SAÍDA DE INSUMOS
    # =====================================

    path('saidas/',
         views.saida_insumo_list,
         name='saida_insumo_list'),

    path('saidas/novo/',
         views.saida_insumo_create,
         name='saida_insumo_create'),

    path('saidas/<int:id>/deletar/',
         views.saida_insumo_delete,
         name='saida_insumo_delete'),

    # =====================================
    # USUÁRIOS
    # =====================================

    path('usuarios_create/',
         views.usuarios_create,
         name='criar_usuario'),

    path('usuarios/',
         views.usuarios_list,
         name='usuarios_list'),

    path('usuarios/<int:id>/editar/',
         views.colaboradores_edit,
         name='usuario_edit'),

    path('usuarios/<int:id>/deletar/',
         views.usuario_delete,
         name='usuario_delete'),

    # =====================================
    # RELATÓRIOS E CHECKLIST
    # =====================================

    path('relatorio-insumos/',
         views.relatorio_insumos,
         name='relatorio_insumos'),

    path('checklist/<str:data_vistoria>/',
         views.visualizar_checklist,
         name='visualizar_checklist'),

    path('checklist/<str:data_vistoria>/excluir/',
         views.excluir_checklist,
         name='excluir_checklist'),

]


# =========================================================
# API REST ROUTER
# =========================================================

router = DefaultRouter()

router.register(r'produtos', ProdutoViewSet)
router.register(r'insumos', InsumoViewSet)
router.register(r'colaboradores', ColaboradorViewSet)


# =========================================================
# API URLs
# =========================================================

urlpatterns += [

    path('api/', include(router.urls)),

]
