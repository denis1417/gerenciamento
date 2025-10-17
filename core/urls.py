from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # Colaboradores
    path('colaboradores/', views.colaboradores_list, name='colaboradores_list'),
    path('colaboradores/novo/', views.colaboradores_create,
         name='colaboradores_create'),
    path('colaboradores/<int:id>/', views.colaboradores_detail,
         name='colaboradores_detail'),
    path('colaboradores/<int:id>/editar/',
         views.colaboradores_edit, name='colaboradores_edit'),
    path('colaboradores/<int:id>/excluir/',
         views.colaboradores_delete, name='colaboradores_delete'),

    # Insumos
    path('insumos/', views.insumos_list, name='insumos_list'),
    path('insumos/novo/', views.insumos_create, name='insumos_create'),
    path('insumos/<int:id>/editar/', views.insumos_edit, name='insumos_edit'),
    path('insumos/<int:id>/deletar/', views.insumos_delete, name='insumos_delete'),

    # Produtos Prontos
    path('produtos/', views.produtos_list, name='produtos_list'),
    path('produtos/novo/', views.produtos_create, name='produtos_create'),
    path('produtos/<int:id>/editar/', views.produtos_edit, name='produtos_edit'),
    path('produtos/<int:id>/deletar/',
         views.produtos_delete, name='produtos_delete'),
    path('catalogo/', views.catalogo_list, name='catalogo_list'),
    path('catalogo/novo/', views.catalogo_create, name='catalogo_create'),
    path('catalogo/<int:pk>/editar/', views.catalogo_edit, name='catalogo_edit'),
    path('catalogo/<int:pk>/deletar/',
         views.catalogo_delete, name='catalogo_delete'),


    # Fichas de Produção
    path('produtos/ficha/criar/', views.criar_ficha, name='criar_ficha'),
    path('produtos/ficha/<int:ficha_id>/visualizar/',
         views.visualizar_ficha, name='visualizar_ficha'),

    # Saída de Insumos
    path('saidas/', views.saida_insumo_list, name='saida_insumo_list'),
    path('saidas/novo/', views.saida_insumo_create, name='saida_insumo_create'),
    path('saidas/<int:id>/deletar/', views.saida_insumo_delete,
         name='saida_insumo_delete'),

    # Criar Usuário
    path('usuarios_create/', views.usuarios_create, name='criar_usuario'),

    # Usuários
    path('usuarios/', views.usuarios_list, name='usuarios_list'),
    path('usuarios/<int:id>/editar/',
         views.colaboradores_edit, name='usuario_edit'),
    path('usuarios/<int:id>/deletar/',
         views.usuario_delete, name='usuario_delete'),

    # Logout
    path('logout/', views.logout_view, name='logout'),

    # Relatório de Insumos (somente Administrador)
    path('relatorio-insumos/', views.relatorio_insumos, name='relatorio_insumos'),
    path('checklist/<str:data_vistoria>/',
         views.visualizar_checklist, name='visualizar_checklist'),
    path('checklist/<str:data_vistoria>/excluir/',
         views.excluir_checklist, name='excluir_checklist'),
]
