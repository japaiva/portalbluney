# gestor/urls.py - CORREÇÃO DA URL consultar_bi

from django.urls import path
from . import views

app_name = 'gestor'

urlpatterns = [
    # ===== DASHBOARD =====
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # ===== CLIENTES =====
    path('clientes/', views.cliente_list, name='cliente_list'),
    path('clientes/criar/', views.cliente_create, name='cliente_create'),
    path('clientes/<int:pk>/', views.cliente_detail, name='cliente_detail'),
    path('clientes/<int:pk>/editar/', views.cliente_update, name='cliente_update'),
    path('clientes/<int:pk>/deletar/', views.cliente_delete, name='cliente_delete'),
    path('clientes/codigo/<str:codigo>/', views.cliente_detail_by_codigo, name='cliente_detail_by_codigo'),
    
    # ===== CONTATOS DE CLIENTES =====
    path('clientes/<int:cliente_id>/contatos/criar/', views.cliente_contato_create, name='cliente_contato_create'),
    path('contatos/<int:pk>/editar/', views.cliente_contato_update, name='cliente_contato_update'),
    path('contatos/<int:pk>/deletar/', views.cliente_contato_delete, name='cliente_contato_delete'),
    
    # ===== LOJAS =====
    path('lojas/', views.loja_list, name='loja_list'),
    path('lojas/criar/', views.loja_create, name='loja_create'),
    path('lojas/<str:pk>/', views.loja_detail, name='loja_detail'),
    path('lojas/<str:pk>/editar/', views.loja_edit, name='loja_edit'),
    path('lojas/<str:pk>/deletar/', views.loja_delete, name='loja_delete'),
    path('lojas/<str:pk>/atualizar/', views.loja_update, name='loja_update'),
    
    # ===== VENDEDORES =====
    path('vendedores/', views.vendedor_list, name='vendedor_list'),
    path('vendedores/criar/', views.vendedor_create, name='vendedor_create'),
    path('vendedores/<str:pk>/', views.vendedor_detail, name='vendedor_detail'),
    path('vendedores/<str:pk>/editar/', views.vendedor_edit, name='vendedor_edit'),
    path('vendedores/<str:pk>/deletar/', views.vendedor_delete, name='vendedor_delete'),
    path('vendedores/<str:pk>/atualizar/', views.vendedor_update, name='vendedor_update'),
    
    # ===== FABRICANTES =====
    path('fabricantes/', views.fabricante_list, name='fabricante_list'),
    path('fabricantes/criar/', views.fabricante_create, name='fabricante_create'),
    path('fabricantes/<str:pk>/', views.fabricante_detail, name='fabricante_detail'),
    path('fabricantes/<str:pk>/editar/', views.fabricante_edit, name='fabricante_edit'),
    path('fabricantes/<str:pk>/deletar/', views.fabricante_delete, name='fabricante_delete'),
    path('fabricantes/<str:pk>/atualizar/', views.fabricante_update, name='fabricante_update'),
    
    # ===== GRUPOS DE PRODUTO =====
    path('grupos/', views.grupo_list, name='grupo_list'),
    path('grupos/criar/', views.grupo_create, name='grupo_create'),
    path('grupos/<str:pk>/editar/', views.grupo_edit, name='grupo_edit'),
    path('grupos/<str:pk>/deletar/', views.grupo_delete, name='grupo_delete'),
    
    path('grupos-produto/', views.grupo_produto_list, name='grupo_produto_list'),
    path('grupos-produto/criar/', views.grupo_produto_create, name='grupo_produto_create'),
    path('grupos-produto/<str:pk>/', views.grupo_produto_detail, name='grupo_produto_detail'),
    path('grupos-produto/<str:pk>/editar/', views.grupo_produto_update, name='grupo_produto_update'),
    path('grupos-produto/<str:pk>/deletar/', views.grupo_produto_delete, name='grupo_produto_delete'),
    
    # ===== PRODUTOS =====
    path('produtos/', views.produto_list, name='produto_list'),
    path('produtos/criar/', views.produto_create, name='produto_create'),
    path('produtos/<str:pk>/', views.produto_detail, name='produto_detail'),
    path('produtos/<str:pk>/editar/', views.produto_edit, name='produto_edit'),
    path('produtos/<str:pk>/deletar/', views.produto_delete, name='produto_delete'),
    path('produtos/<str:pk>/atualizar/', views.produto_update, name='produto_update'),
    
    # ===== VENDAS =====
    path('vendas/', views.vendas_list, name='vendas_list'),
    path('vendas/criar/', views.vendas_create, name='vendas_create'),
    path('vendas/<int:pk>/', views.vendas_detail, name='vendas_detail'),
    path('vendas/<int:pk>/editar/', views.vendas_edit, name='vendas_edit'),
    path('vendas/<int:pk>/deletar/', views.vendas_delete, name='vendas_delete'),
    path('vendas/<int:pk>/atualizar/', views.vendas_update, name='vendas_update'),
    
    # ===== IMPORTAÇÃO =====
    path('importar-vendas/', views.importar_vendas, name='importar_vendas'),
    
    # ===== SINCRONIZAÇÃO =====
    path('sincronizacao/', views.sincronizacao_dashboard, name='sincronizacao_dashboard'),
    path('sincronizacao/bi/', views.sincronizar_bi, name='sincronizar_bi'),
    path('sincronizacao/receita/', views.sincronizar_receita, name='sincronizar_receita'),
    path('sincronizacao/completa/', views.sincronizacao_completa, name='sincronizacao_completa'),
    
    # ===== USUÁRIOS =====
    path('usuarios/', views.usuario_list, name='usuario_list'),
    path('usuarios/criar/', views.usuario_create, name='usuario_create'),
    path('usuarios/<int:pk>/', views.usuario_detail, name='usuario_detail'),
    path('usuarios/<int:pk>/editar/', views.usuario_update, name='usuario_update'),
    path('usuarios/<int:pk>/deletar/', views.usuario_delete, name='usuario_delete'),
    
    # ===== RELATÓRIOS =====
    path('relatorio-clientes/', views.relatorio_clientes, name='relatorio_clientes'),
    
    # ===== APIs (Cliente) =====
    path('api/vendedor/<str:codigo>/', views.api_vendedor_por_codigo, name='api_vendedor_por_codigo'),
    path('api/cliente/<str:codigo>/', views.api_cliente_por_codigo, name='api_cliente_por_codigo'),
    path('api/consultar-receita/<str:cpf_cnpj>/', views.api_consultar_receita, name='api_consultar_receita'),
    
    # ===== APIs (Gerais) =====
    path('api/vendedor-por-codigo/<str:codigo>/', views.vendedor_por_codigo, name='vendedor_por_codigo'),
    path('api/cliente-por-codigo/<str:codigo>/', views.cliente_por_codigo, name='cliente_por_codigo'),
    path('api/consultar-receita-geral/<str:cpf_cnpj>/', views.consultar_receita, name='consultar_receita_geral'),
    
    # *** 🔥 CORREÇÃO AQUI: ADICIONAR PARÂMETRO À URL ***
    path('api/consultar-bi/<str:codigo>/', views.consultar_bi, name='consultar_bi'),
    
    # ===== APIs (Produtos) - NOVAS =====
    path('api/produtos/buscar/', views.buscar_produtos_api, name='api_buscar_produtos'),
    path('api/produtos/<str:codigo>/', views.produto_detail_api, name='api_produto_detail'),
    path('api/produtos/lista/', views.produtos_lista_api, name='api_produtos_lista'),
    path('api/grupos-produtos/', views.grupos_produtos_api, name='api_grupos_produtos'),
    path('api/fabricantes/', views.fabricantes_api, name='api_fabricantes'),
    path('api/produtos/debug/', views.debug_produtos_api, name='api_debug_produtos'),
]
