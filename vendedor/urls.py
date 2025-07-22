# vendedor/urls.py - VERSÃO FINAL COMPLETA

from django.urls import path
from . import views

app_name = 'vendedor'

urlpatterns = [
    # ===== HOME E DASHBOARD =====
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # ===== CLIENTES (SOMENTE VISUALIZAÇÃO) =====
    path('clientes/', views.cliente_list, name='cliente_list'),
    path('clientes/<int:pk>/', views.cliente_detail, name='cliente_detail'),
    path('clientes/codigo/<str:codigo>/', views.cliente_detail_by_codigo, name='cliente_detail_by_codigo'),
    
    # ===== VENDAS (SOMENTE VISUALIZAÇÃO) =====
    path('vendas/', views.vendas_list, name='vendas_list'),
    path('vendas/<int:pk>/', views.vendas_detail, name='vendas_detail'),
    

    path('api/consultar-bi/<str:codigo>/', views.consultar_bi, name='consultar_bi'),
    
    # ===== APIs PARA AJAX (SOMENTE CONSULTA) =====
    path('api/vendedor-por-codigo/<str:codigo>/', views.api_vendedor_por_codigo, name='api_vendedor_por_codigo'),
    path('api/cliente-por-codigo/<str:codigo>/', views.api_cliente_por_codigo, name='api_cliente_por_codigo'),
    path('api/consultar-receita/<str:cpf_cnpj>/', views.api_consultar_receita, name='api_consultar_receita'),
    path('api/buscar-produtos/', views.api_buscar_produtos, name='api_buscar_produtos'),
    
    # ===== RELATÓRIOS =====
    path('relatorios/clientes/', views.relatorio_clientes, name='relatorio_clientes'),
]