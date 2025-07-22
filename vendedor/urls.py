# vendedor/urls.py

from django.urls import path
from . import views

app_name = 'vendedor'

urlpatterns = [
    # ===== DASHBOARD =====
    path('', views.dashboard, name='dashboard'),
    
    # ===== CLIENTES =====
    path('clientes/', views.listar_clientes, name='listar_clientes'),
    path('clientes/<str:codigo>/', views.detalhar_cliente, name='detalhar_cliente'),
    path('clientes/<str:codigo>/editar/', views.editar_cliente, name='editar_cliente'),
    
    # ===== CONTATOS =====
    path('clientes/<str:codigo_cliente>/contatos/', views.listar_contatos, name='listar_contatos'),
    path('clientes/<str:codigo_cliente>/contatos/adicionar/', views.adicionar_contato, name='adicionar_contato'),
    
    # ===== HISTÓRICO DE VENDAS =====
    path('clientes/<str:codigo_cliente>/vendas/', views.historico_vendas, name='historico_vendas'),
    
    # ===== RELATÓRIOS =====
    path('relatorios/vendas/', views.relatorio_vendas, name='relatorio_vendas'),
]