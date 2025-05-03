# gestor/views/cliente.py

import logging
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.db.models import Q

from core.models import Cliente, ClienteContato, ClienteItem
from core.forms import ClienteForm, ClienteContatoForm, ClienteItemForm
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)


# Gerenciamento de Contatos (renomeado para ClienteContato)
@login_required
def cliente_contato_create(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    
    if request.method == 'POST':
        form = ClienteContatoForm(request.POST)
        if form.is_valid():
            contato = form.save(commit=False)
            contato.cliente = cliente
            contato.codigo_master = cliente.codigo  # Define o código master
            
            # Se este contato está marcado como principal, remover esta marca de outros
            if contato.principal:
                cliente.contatos.filter(principal=True).update(principal=False)
            
            contato.save()
            messages.success(request, 'Contato adicionado com sucesso.')
            return redirect('gestor:cliente_detail', pk=cliente.id)
    else:
        form = ClienteContatoForm()
    
    return render(request, 'gestor/cliente_contato_form.html', {
        'form': form, 
        'cliente': cliente
    })

@login_required
def cliente_contato_update(request, pk):
    contato = get_object_or_404(ClienteContato, pk=pk)
    cliente = contato.cliente
    
    if request.method == 'POST':
        form = ClienteContatoForm(request.POST, instance=contato)
        if form.is_valid():
            # Se este contato está marcado como principal, remover esta marca de outros
            if form.cleaned_data['principal']:
                cliente.contatos.exclude(pk=contato.pk).filter(principal=True).update(principal=False)
            
            contato = form.save()
            messages.success(request, 'Contato atualizado com sucesso.')
            return redirect('gestor:cliente_detail', pk=cliente.id)
    else:
        form = ClienteContatoForm(instance=contato)
    
    return render(request, 'gestor/cliente_contato_form.html', {
        'form': form, 
        'cliente': cliente,
        'contato': contato
    })

@login_required
def cliente_contato_delete(request, pk):
    contato = get_object_or_404(ClienteContato, pk=pk)
    cliente = contato.cliente
    
    if request.method == 'POST':
        contato.delete()
        messages.success(request, 'Contato excluído com sucesso.')
        return redirect('gestor:cliente_detail', pk=cliente.id)
    
    return render(request, 'gestor/cliente_contato_confirm_delete.html', {
        'contato': contato,
        'cliente': cliente
    })

# Gerenciamento de Itens (CPF/CNPJ)
@login_required
def cliente_item_create(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    
    if request.method == 'POST':
        form = ClienteItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.cliente = cliente
            item.codigo_master = cliente.codigo  # Define o código master
            item.save()
            messages.success(request, 'Item adicionado com sucesso.')
            return redirect('gestor:cliente_detail', pk=cliente.id)
    else:
        form = ClienteItemForm()
    
    return render(request, 'gestor/cliente_item_form.html', {
        'form': form, 
        'cliente': cliente
    })

@login_required
def cliente_item_update(request, pk):
    item = get_object_or_404(ClienteItem, pk=pk)
    cliente = item.cliente
    
    if request.method == 'POST':
        form = ClienteItemForm(request.POST, instance=item)
        if form.is_valid():
            item = form.save()
            messages.success(request, 'Item atualizado com sucesso.')
            return redirect('gestor:cliente_detail', pk=cliente.id)
    else:
        form = ClienteItemForm(instance=item)
    
    return render(request, 'gestor/cliente_item_form.html', {
        'form': form, 
        'cliente': cliente,
        'item': item
    })

@login_required
def cliente_item_delete(request, pk):
    item = get_object_or_404(ClienteItem, pk=pk)
    cliente = item.cliente
    
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Item excluído com sucesso.')
        return redirect('gestor:cliente_detail', pk=cliente.id)
    
    return render(request, 'gestor/cliente_item_confirm_delete.html', {
        'item': item,
        'cliente': cliente
    })

@login_required
def cliente_list(request):
    clientes_list = Cliente.objects.all().order_by('nome')
    
    # Filtro por status
    status = request.GET.get('status')
    if status == 'ativo':
        clientes_list = clientes_list.filter(ativo=True)
    elif status == 'inativo':
        clientes_list = clientes_list.filter(ativo=False)
    
    # Busca por nome ou código
    query = request.GET.get('q')
    if query:
        clientes_list = clientes_list.filter(
            Q(nome__icontains=query) | Q(codigo__icontains=query)
        )
    
    # Paginação
    paginator = Paginator(clientes_list, 10)
    page = request.GET.get('page', 1)
    
    try:
        clientes = paginator.page(page)
    except PageNotAnInteger:
        clientes = paginator.page(1)
    except EmptyPage:
        clientes = paginator.page(paginator.num_pages)
    
    return render(request, 'gestor/cliente_list.html', {
        'clientes': clientes, 
        'status_filtro': status,
        'query': query
    })

@login_required
def cliente_create(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f'Cliente "{cliente.nome}" cadastrado com sucesso.')
            return redirect('gestor:cliente_list')
    else:
        form = ClienteForm()
    
    return render(request, 'gestor/cliente_form.html', {'form': form})

@login_required
def cliente_update(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f'Cliente "{cliente.nome}" atualizado com sucesso.')
            return redirect('gestor:cliente_list')
    else:
        form = ClienteForm(instance=cliente)
    
    return render(request, 'gestor/cliente_form.html', {'form': form, 'cliente': cliente})

@login_required
def cliente_toggle_status(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    cliente.ativo = not cliente.ativo
    cliente.save()
    
    status = "ativado" if cliente.ativo else "desativado"
    messages.success(request, f'Cliente "{cliente.nome}" {status} com sucesso.')
    
    return redirect('gestor:cliente_list')

@login_required
def cliente_detail(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    contatos = cliente.contatos.all()
    itens = cliente.itens.all()
    
    # Formulários para adicionar novo contato e item
    contato_form = ContatoForm()
    item_form = ClienteItemForm()
    
    return render(request, 'gestor/cliente_detail.html', {
        'cliente': cliente,
        'contatos': contatos,
        'itens': itens,
        'contato_form': contato_form,
        'item_form': item_form
    })

# gestor/views.py ou gestor/views/cliente.py
@login_required
def home(request):
    """
    Página inicial do Portal do Gestor
    """
    return render(request, 'gestor/home.html')

@login_required
def dashboard(request):
    """View para o dashboard do gestor"""
    return render(request, 'gestor/dashboard.html')

@login_required
def cliente_detail(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    contatos = cliente.contatos.all()
    itens = cliente.itens.all()
    
    # Formulários para adicionar novo contato e item
    contato_form = ClienteContatoForm()  # Alterado de ContatoForm para ClienteContatoForm
    item_form = ClienteItemForm()
    
    return render(request, 'gestor/cliente_detail.html', {
        'cliente': cliente,
        'contatos': contatos,
        'itens': itens,
        'contato_form': contato_form,
        'item_form': item_form
    })