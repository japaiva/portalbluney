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
    
    # Cliente
    path('clientes/', views.cliente_list, name='cliente_list'),
    path('clientes/novo/', views.cliente_create, name='cliente_create'),
    path('clientes/<int:pk>/', views.cliente_detail, name='cliente_detail'),
    path('clientes/<int:pk>/editar/', views.cliente_update, name='cliente_update'),
    path('clientes/<int:pk>/alternar-status/', views.cliente_toggle_status, name='cliente_toggle_status'),
    path('clientes/codigo/<str:codigo>/', views.cliente_detail_by_codigo, name='cliente_detail_by_codigo'),
    
    # Contatos de Cliente
    path('clientes/<int:cliente_id>/contatos/novo/', views.cliente_contato_create, name='cliente_contato_create'),
    path('clientes/contatos/<int:pk>/editar/', views.cliente_contato_update, name='cliente_contato_update'),
    path('clientes/contatos/<int:pk>/excluir/', views.cliente_contato_delete, name='cliente_contato_delete'),
    
    # API para consultas
    path('api/cliente-por-codigo/<str:codigo>/', views.api_cliente_por_codigo, name='api_cliente_por_codigo'),
    path('api/consultar-receita/<str:cpf_cnpj>/', views.api_consultar_receita, name='api_consultar_receita'),
    
    # BI
    path('clientes/<str:codigo_cliente>/bi/', views.consultar_bi, name='consultar_bi'),
]