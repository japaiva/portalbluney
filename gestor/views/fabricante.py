# gestor/views/fabricante.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from core.models import Fabricante
from core.forms import FabricanteForm

@login_required
def fabricante_list(request):
    """Lista de fabricantes"""
    search = request.GET.get('search', '')
    fabricantes = Fabricante.objects.all()
    
    if search:
        fabricantes = fabricantes.filter(
            Q(codigo__icontains=search) |
            Q(descricao__icontains=search)
        )
    
    context = {'fabricantes': fabricantes, 'search': search}
    return render(request, 'gestor/fabricante_list.html', context)

@login_required
def fabricante_create(request):
    """Criar novo fabricante"""
    if request.method == 'POST':
        form = FabricanteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fabricante criado com sucesso!')
            return redirect('gestor:fabricante_list')
    else:
        form = FabricanteForm()
    
    context = {'form': form, 'title': 'Novo Fabricante'}
    return render(request, 'gestor/fabricante_form.html', context)

@login_required
def fabricante_edit(request, pk):
    """Editar fabricante"""
    fabricante = get_object_or_404(Fabricante, codigo=pk)
    
    if request.method == 'POST':
        form = FabricanteForm(request.POST, instance=fabricante)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fabricante atualizado com sucesso!')
            return redirect('gestor:fabricante_list')
    else:
        form = FabricanteForm(instance=fabricante)
    
    context = {'form': form, 'title': 'Editar Fabricante', 'fabricante': fabricante}
    return render(request, 'gestor/fabricante_form.html', context)

@login_required
def fabricante_delete(request, pk):
    """Deletar fabricante"""
    fabricante = get_object_or_404(Fabricante, codigo=pk)
    
    if request.method == 'POST':
        fabricante.delete()
        messages.success(request, 'Fabricante excluído com sucesso!')
        return redirect('gestor:fabricante_list')
    
    context = {'fabricante': fabricante}
    return render(request, 'gestor/fabricante_confirm_delete.html', context)

@login_required
def fabricante_detail(request, pk):
    """Detalhes do fabricante"""
    fabricante = get_object_or_404(Fabricante, codigo=pk)
    produtos = fabricante.produtos.all()[:10]  # Últimos 10 produtos
    
    context = {
        'fabricante': fabricante,
        'produtos': produtos
    }
    return render(request, 'gestor/fabricante_detail.html', context)

@login_required
def fabricante_update(request, pk):
    """View para editar fabricante (alias para fabricante_edit)"""
    return fabricante_edit(request, pk)