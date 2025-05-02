# gestor/urls.py
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse


from django.urls import path
from . import views


from core.views import (
    GestorLoginView
)


app_name = 'gestor'

urlpatterns = [


    # Nova URL para login usando a view importada do core
    path('login/', GestorLoginView.as_view(), name='login'),
    
    # Páginas principais
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # CRUD Usuário
    path('usuarios/', views.usuario_list, name='usuario_list'),
    path('usuarios/novo/', views.usuario_create, name='usuario_create'),
    path('usuarios/<int:pk>/editar/', views.usuario_update, name='usuario_update'),
    path('usuarios/<int:pk>/alternar-status/', views.usuario_toggle_status, name='usuario_toggle_status'),


    # CRUD Clientes
    path('clientes/', views.cliente_list, name='cliente_list'),
    path('clientes/novo/', views.cliente_create, name='cliente_create'),
    path('clientes/<int:pk>/', views.cliente_detail, name='cliente_detail'),
    path('clientes/<int:pk>/editar/', views.cliente_update, name='cliente_update'),
    path('clientes/<int:pk>/alternar-status/', views.cliente_toggle_status, name='cliente_toggle_status'),

    # Contatos
    path('clientes/<int:cliente_id>/contatos/novo/', views.contato_create, name='contato_create'),
    path('contatos/<int:pk>/editar/', views.contato_update, name='contato_update'),
    path('contatos/<int:pk>/excluir/', views.contato_delete, name='contato_delete'),

    # Itens de Cliente (CPF/CNPJ)
    path('clientes/<int:cliente_id>/itens/novo/', views.cliente_item_create, name='cliente_item_create'),
    path('itens/<int:pk>/editar/', views.cliente_item_update, name='cliente_item_update'),
    path('itens/<int:pk>/excluir/', views.cliente_item_delete, name='cliente_item_delete'),
]


