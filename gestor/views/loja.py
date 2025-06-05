# gestor/views/loja.py

from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone

from core.models import Loja, Vendas
from core.forms import LojaForm

@login_required
def loja_list(request):
    """Lista de lojas"""
    search = request.GET.get('search', '')
    lojas = Loja.objects.all()
    
    if search:
        lojas = lojas.filter(
            Q(codigo__icontains=search) |
            Q(nome__icontains=search)
        )
    
    context = {'lojas': lojas, 'search': search}
    return render(request, 'gestor/loja_list.html', context)

@login_required
def loja_create(request):
    """Criar nova loja"""
    if request.method == 'POST':
        form = LojaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Loja criada com sucesso!')
            return redirect('gestor:loja_list')
    else:
        form = LojaForm()
    
    context = {'form': form, 'title': 'Nova Loja'}
    return render(request, 'gestor/loja_form.html', context)

@login_required
def loja_edit(request, pk):
    """Editar loja"""
    loja = get_object_or_404(Loja, codigo=pk)
    
    if request.method == 'POST':
        form = LojaForm(request.POST, instance=loja)
        if form.is_valid():
            form.save()
            messages.success(request, 'Loja atualizada com sucesso!')
            return redirect('gestor:loja_list')
    else:
        form = LojaForm(instance=loja)
    
    context = {'form': form, 'title': 'Editar Loja', 'loja': loja}
    return render(request, 'gestor/loja_form.html', context)

@login_required
def loja_delete(request, pk):
    """Deletar loja"""
    loja = get_object_or_404(Loja, codigo=pk)
    
    if request.method == 'POST':
        loja.delete()
        messages.success(request, 'Loja excluída com sucesso!')
        return redirect('gestor:loja_list')
    
    context = {'loja': loja}
    return render(request, 'gestor/loja_confirm_delete.html', context)

@login_required
def loja_detail(request, pk):
    """Detalhes da loja"""
    loja = get_object_or_404(Loja, codigo=pk)
    
    # Buscar vendedores desta loja
    vendedores = loja.vendedores.all().order_by('nome')
    
    # Buscar vendas recentes desta loja (últimos 30 dias)
    data_limite = timezone.now().date() - timedelta(days=30)
    vendas_recentes = Vendas.objects.filter(
        loja=loja,
        data_venda__gte=data_limite
    ).order_by('-data_venda')[:10]
    
    context = {
        'loja': loja,
        'vendedores': vendedores,
        'vendas_recentes': vendas_recentes
    }
    return render(request, 'gestor/loja_detail.html', context)

@login_required
def loja_update(request, pk):
    """View para editar loja (alias para loja_edit)"""
    return loja_edit(request, pk)