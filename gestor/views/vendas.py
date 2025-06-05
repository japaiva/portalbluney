# gestor/views/vendas.py

import logging
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from core.models import Vendas, Loja, Vendedor
from core.forms import VendasForm

logger = logging.getLogger(__name__)

@login_required
def vendas_list(request):
    """Lista de vendas com filtros"""
    # Filtros múltiplos
    search = request.GET.get('search', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    loja_filtro = request.GET.get('loja', '')
    vendedor_filtro = request.GET.get('vendedor', '')
    
    vendas_list = Vendas.objects.select_related(
        'cliente', 'produto', 'produto__grupo', 'produto__fabricante', 
        'loja', 'vendedor'
    ).all()
    
    # Aplicar filtros
    if search:
        vendas_list = vendas_list.filter(
            Q(cliente__nome__icontains=search) |
            Q(cliente__codigo__icontains=search) |
            Q(produto__descricao__icontains=search) |
            Q(produto__codigo__icontains=search) |
            Q(numero_nf__icontains=search)
        )
    
    if data_inicio:
        try:
            data_inicio_parsed = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            vendas_list = vendas_list.filter(data_venda__gte=data_inicio_parsed)
        except ValueError:
            pass
    
    if data_fim:
        try:
            data_fim_parsed = datetime.strptime(data_fim, '%Y-%m-%d').date()
            vendas_list = vendas_list.filter(data_venda__lte=data_fim_parsed)
        except ValueError:
            pass
    
    if loja_filtro:
        vendas_list = vendas_list.filter(loja__codigo=loja_filtro)
    
    if vendedor_filtro:
        vendas_list = vendas_list.filter(vendedor__codigo=vendedor_filtro)
    
    # Ordenação
    vendas_list = vendas_list.order_by('-data_venda', '-id')
    
    # Paginação
    paginator = Paginator(vendas_list, 20)
    page = request.GET.get('page', 1)
    
    try:
        vendas = paginator.page(page)
    except PageNotAnInteger:
        vendas = paginator.page(1)
    except EmptyPage:
        vendas = paginator.page(paginator.num_pages)
    
    # Dados para filtros
    lojas_disponiveis = Loja.objects.filter(ativo=True).order_by('codigo')
    vendedores_disponiveis = Vendedor.objects.filter(ativo=True).order_by('nome')
    
    # Calcular totais da página atual
    total_quantidade = sum(v.quantidade for v in vendas)
    total_valor = sum(v.valor_total for v in vendas)
    
    context = {
        'vendas': vendas,
        'search': search,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'loja_filtro': loja_filtro,
        'vendedor_filtro': vendedor_filtro,
        'lojas_disponiveis': lojas_disponiveis,
        'vendedores_disponiveis': vendedores_disponiveis,
        'total_quantidade': total_quantidade,
        'total_valor': total_valor,
    }
    
    return render(request, 'gestor/vendas_list.html', context)

@login_required
def vendas_create(request):
    """Criar nova venda"""
    if request.method == 'POST':
        form = VendasForm(request.POST)
        if form.is_valid():
            try:
                venda = form.save()
                messages.success(request, f'Venda para {venda.cliente.nome} criada com sucesso!')
                return redirect('gestor:vendas_list')
            except Exception as e:
                logger.error(f"Erro ao criar venda: {str(e)}")
                messages.error(request, f'Erro ao criar venda: {str(e)}')
        else:
            messages.error(request, 'Corrija os erros abaixo.')
    else:
        form = VendasForm()
    
    context = {
        'form': form, 
        'title': 'Nova Venda',
        'is_create': True
    }
    return render(request, 'gestor/vendas_form.html', context)

@login_required
def vendas_edit(request, pk):
    """Editar venda"""
    venda = get_object_or_404(Vendas, pk=pk)
    
    if request.method == 'POST':
        form = VendasForm(request.POST, instance=venda)
        if form.is_valid():
            try:
                venda = form.save()
                messages.success(request, f'Venda para {venda.cliente.nome} atualizada com sucesso!')
                return redirect('gestor:vendas_list')
            except Exception as e:
                logger.error(f"Erro ao atualizar venda: {str(e)}")
                messages.error(request, f'Erro ao atualizar venda: {str(e)}')
        else:
            messages.error(request, 'Corrija os erros abaixo.')
    else:
        form = VendasForm(instance=venda)
    
    context = {
        'form': form, 
        'title': f'Editar Venda #{venda.id}',
        'venda': venda,
        'is_edit': True
    }
    return render(request, 'gestor/vendas_form.html', context)

@login_required
def vendas_detail(request, pk):
    """Detalhes da venda"""
    venda = get_object_or_404(Vendas.objects.select_related(
        'cliente', 'produto', 'grupo_produto', 'fabricante', 
        'loja', 'vendedor'
    ), pk=pk)
    
    # Buscar outras vendas do mesmo cliente
    vendas_relacionadas = Vendas.objects.filter(
        cliente=venda.cliente
    ).exclude(pk=venda.pk).order_by('-data_venda')[:5]
    
    context = {
        'venda': venda,
        'vendas_relacionadas': vendas_relacionadas,
    }
    
    return render(request, 'gestor/vendas_detail.html', context)

@login_required
def vendas_delete(request, pk):
    """Deletar venda"""
    venda = get_object_or_404(Vendas, pk=pk)
    
    if request.method == 'POST':
        cliente_nome = venda.cliente.nome
        venda_id = venda.id
        venda.delete()
        messages.success(request, f'Venda #{venda_id} de {cliente_nome} excluída com sucesso!')
        return redirect('gestor:vendas_list')
    
    context = {
        'venda': venda
    }
    return render(request, 'gestor/vendas_confirm_delete.html', context)

@login_required
def vendas_update(request, pk):
    """View para editar venda (alias para vendas_edit)"""
    return vendas_edit(request, pk)