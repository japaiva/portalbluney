# vendedor/views/vendas.py - VERSÃO SOMENTE LEITURA

import logging
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Sum

from core.models import Vendas, Loja, Vendedor

logger = logging.getLogger(__name__)

@login_required
def vendas_list(request):
    """Lista de vendas com filtros - SOMENTE LEITURA"""
    # Base queryset
    vendas_list = Vendas.objects.select_related(
        'cliente', 'produto', 'produto__grupo', 'produto__fabricante', 
        'loja'
    ).all()
    
    # Filtro por vendedor (se usuário é vendedor, mostrar apenas suas vendas)
    if request.user.nivel == 'vendedor' and request.user.codigo_vendedor:
        vendas_list = vendas_list.filter(cliente__codigo_vendedor=request.user.codigo_vendedor)
    
    # Filtros
    search = request.GET.get('search', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    loja_filtro = request.GET.get('loja', '')
    vendedor_filtro = request.GET.get('vendedor', '')
    
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
    
    if vendedor_filtro and request.user.nivel in ['admin', 'gestor']:
        vendas_list = vendas_list.filter(cliente__codigo_vendedor=vendedor_filtro)
    
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
    
    # Dados para filtros (apenas para gestores/admins)
    if request.user.nivel in ['admin', 'gestor']:
        lojas_disponiveis = Loja.objects.filter(ativo=True).order_by('codigo')
        vendedores_disponiveis = Vendedor.objects.filter(ativo=True).order_by('nome')
    else:
        lojas_disponiveis = []
        vendedores_disponiveis = []
    
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
        'is_readonly': True,  # Indica que é somente leitura
    }
    
    return render(request, 'vendedor/vendas_list.html', context)

@login_required
def vendas_detail(request, pk):
    """Detalhes da venda - SOMENTE VISUALIZAÇÃO"""
    venda = get_object_or_404(Vendas.objects.select_related(
        'cliente', 'produto', 'produto__grupo', 'produto__fabricante', 
        'loja'
    ), pk=pk)
    
    # Verificar se vendedor pode ver esta venda
    if request.user.nivel == 'vendedor' and request.user.codigo_vendedor:
        if venda.cliente.codigo_vendedor != request.user.codigo_vendedor:
            from django.contrib import messages
            messages.error(request, 'Você só pode visualizar vendas de seus clientes.')
            return redirect('vendedor:vendas_list')
    
    # Buscar outras vendas do mesmo cliente
    vendas_relacionadas = Vendas.objects.filter(
        cliente=venda.cliente
    ).exclude(pk=venda.pk).order_by('-data_venda')[:5]
    
    context = {
        'venda': venda,
        'vendas_relacionadas': vendas_relacionadas,
        'is_readonly': True,  # Indica que é somente leitura
    }
    
    return render(request, 'vendedor/vendas_detail.html', context)