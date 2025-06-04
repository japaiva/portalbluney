# gestor/urls.py
from django.urls import path
from . import views
from core.views import GestorLoginView

app_name = 'gestor'

urlpatterns = [
    # Página de login
    path('login/', GestorLoginView.as_view(), name='login'),
    
    # Páginas principais
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # ===== CLIENTE =====
    path('clientes/', views.cliente_list, name='cliente_list'),
    path('clientes/novo/', views.cliente_create, name='cliente_create'),
    path('clientes/<int:pk>/', views.cliente_detail, name='cliente_detail'),
    path('clientes/<int:pk>/editar/', views.cliente_update, name='cliente_update'),
    path('clientes/<int:pk>/excluir/', views.cliente_delete, name='cliente_delete'),
    path('clientes/codigo/<str:codigo>/', views.cliente_detail_by_codigo, name='cliente_detail_by_codigo'),
    
    # Contatos de Cliente
    path('clientes/<int:cliente_id>/contatos/novo/', views.cliente_contato_create, name='cliente_contato_create'),
    path('clientes/contatos/<int:pk>/editar/', views.cliente_contato_update, name='cliente_contato_update'),
    path('clientes/contatos/<int:pk>/excluir/', views.cliente_contato_delete, name='cliente_contato_delete'),
    
    # ===== LOJA =====
    path('lojas/', views.loja_list, name='loja_list'),
    path('lojas/nova/', views.loja_create, name='loja_create'),
    path('lojas/<str:pk>/editar/', views.loja_edit, name='loja_edit'),
    path('lojas/<str:pk>/excluir/', views.loja_delete, name='loja_delete'),
    
    # ===== VENDEDOR =====
    path('vendedores/', views.vendedor_list, name='vendedor_list'),
    path('vendedores/novo/', views.vendedor_create, name='vendedor_create'),
    path('vendedores/<str:pk>/editar/', views.vendedor_edit, name='vendedor_edit'),
    path('vendedores/<str:pk>/excluir/', views.vendedor_delete, name='vendedor_delete'),
    
    # ===== FABRICANTE =====
    path('fabricantes/', views.fabricante_list, name='fabricante_list'),
    path('fabricantes/novo/', views.fabricante_create, name='fabricante_create'),
    path('fabricantes/<str:pk>/editar/', views.fabricante_edit, name='fabricante_edit'),
    path('fabricantes/<str:pk>/excluir/', views.fabricante_delete, name='fabricante_delete'),
    
    # ===== GRUPO PRODUTO =====
    path('grupos/', views.grupo_list, name='grupo_list'),
    path('grupos/novo/', views.grupo_create, name='grupo_create'),
    path('grupos/<str:pk>/editar/', views.grupo_edit, name='grupo_edit'),
    path('grupos/<str:pk>/excluir/', views.grupo_delete, name='grupo_delete'),
    
    # ===== PRODUTO =====
    path('produtos/', views.produto_list, name='produto_list'),
    path('produtos/novo/', views.produto_create, name='produto_create'),
    path('produtos/<str:pk>/editar/', views.produto_edit, name='produto_edit'),
    path('produtos/<str:pk>/excluir/', views.produto_delete, name='produto_delete'),
    

    # URLs para vendas
    path('vendas/', views.vendas_list, name='vendas_list'),
    path('vendas/nova/', views.vendas_create, name='vendas_create'),
    path('vendas/<int:pk>/', views.vendas_detail, name='vendas_detail'),
    path('vendas/<int:pk>/editar/', views.vendas_edit, name='vendas_edit'),
    path('vendas/<int:pk>/excluir/', views.vendas_delete, name='vendas_delete'),
        
    # ===== IMPORTAÇÃO =====
    path('vendas/importar/', views.importar_vendas, name='importar_vendas'),
    
    # ===== API PARA CONSULTAS =====
    path('api/cliente-por-codigo/<str:codigo>/', views.api_cliente_por_codigo, name='api_cliente_por_codigo'),
    path('api/consultar-receita/<str:cpf_cnpj>/', views.api_consultar_receita, name='api_consultar_receita'),
    
    # ===== BI =====
    path('clientes/<str:codigo_cliente>/bi/', views.consultar_bi, name='consultar_bi'),
]