# gestor/views/vendedor.py

import logging
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone

from core.models import Vendedor, Vendas
from core.forms import VendedorForm

logger = logging.getLogger(__name__)

@login_required
def vendedor_list(request):
    """Lista de vendedores"""
    search = request.GET.get('search', '')
    vendedores = Vendedor.objects.select_related('loja').all()
    
    if search:
        vendedores = vendedores.filter(
            Q(codigo__icontains=search) |
            Q(nome__icontains=search) |
            Q(loja__nome__icontains=search)
        )
    
    # Ordenar por código
    vendedores = vendedores.order_by('codigo')
    
    context = {
        'vendedores': vendedores, 
        'search': search
    }
    return render(request, 'gestor/vendedor_list.html', context)

@login_required
def vendedor_create(request):
    """Criar novo vendedor"""
    if request.method == 'POST':
        form = VendedorForm(request.POST)
        if form.is_valid():
            try:
                vendedor = form.save()
                messages.success(request, f'Vendedor "{vendedor.nome}" criado com sucesso!')
                return redirect('gestor:vendedor_list')
            except Exception as e:
                messages.error(request, f'Erro ao criar vendedor: {str(e)}')
        else:
            messages.error(request, 'Corrija os erros abaixo.')
    else:
        form = VendedorForm()
    
    context = {
        'form': form, 
        'title': 'Novo Vendedor',
        'is_create': True
    }
    return render(request, 'gestor/vendedor_form.html', context)

@login_required
def vendedor_edit(request, pk):
    """Editar vendedor"""
    try:
        vendedor = get_object_or_404(Vendedor, codigo=pk)
    except Exception as e:
        messages.error(request, f'Vendedor com código "{pk}" não encontrado.')
        return redirect('gestor:vendedor_list')
    
    if request.method == 'POST':
        form = VendedorForm(request.POST, instance=vendedor)
        if form.is_valid():
            try:
                vendedor = form.save()
                messages.success(request, f'Vendedor "{vendedor.nome}" atualizado com sucesso!')
                return redirect('gestor:vendedor_list')
            except Exception as e:
                messages.error(request, f'Erro ao atualizar vendedor: {str(e)}')
        else:
            messages.error(request, 'Corrija os erros abaixo.')
    else:
        form = VendedorForm(instance=vendedor)
    
    context = {
        'form': form, 
        'title': f'Editar Vendedor - {vendedor.nome}',
        'vendedor': vendedor,
        'is_edit': True
    }
    return render(request, 'gestor/vendedor_form.html', context)

@login_required
def vendedor_delete(request, pk):
    """Deletar vendedor"""
    try:
        vendedor = get_object_or_404(Vendedor, codigo=pk)
    except Exception as e:
        messages.error(request, f'Vendedor com código "{pk}" não encontrado.')
        return redirect('gestor:vendedor_list')
    
    if request.method == 'POST':
        try:
            vendedor_nome = vendedor.nome
            vendedor.delete()
            messages.success(request, f'Vendedor "{vendedor_nome}" excluído com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao excluir vendedor: {str(e)}')
        return redirect('gestor:vendedor_list')
    
    # Verificar se o vendedor tem vendas associadas
    vendas_count = vendedor.vendas_set.count() if hasattr(vendedor, 'vendas_set') else 0
    
    context = {
        'vendedor': vendedor,
        'vendas_count': vendas_count
    }
    return render(request, 'gestor/vendedor_confirm_delete.html', context)

@login_required
def vendedor_detail(request, pk):
    """Detalhes do vendedor"""
    vendedor = get_object_or_404(Vendedor, codigo=pk)
    
    # Buscar vendas recentes deste vendedor (últimos 30 dias)
    data_limite = timezone.now().date() - timedelta(days=30)
    vendas_recentes = Vendas.objects.filter(
        vendedor=vendedor,
        data_venda__gte=data_limite
    ).order_by('-data_venda')[:10]
    
    # Calcular totais
    total_vendas = vendas_recentes.aggregate(
        total_valor=Sum('valor_total'),
        total_quantidade=Sum('quantidade')
    )
    
    context = {
        'vendedor': vendedor,
        'vendas_recentes': vendas_recentes,
        'total_valor': total_vendas['total_valor'] or 0,
        'total_quantidade': total_vendas['total_quantidade'] or 0
    }
    return render(request, 'gestor/vendedor_detail.html', context)

@login_required
def vendedor_update(request, pk):
    """View para editar vendedor (alias para vendedor_edit)"""
    return vendedor_edit(request, pk)