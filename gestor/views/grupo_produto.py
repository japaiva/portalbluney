# gestor/views/grupo_produto.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from core.models import GrupoProduto
from core.forms import GrupoProdutoForm

@login_required
def grupo_list(request):
    """Lista de grupos de produto"""
    search = request.GET.get('search', '')
    grupos = GrupoProduto.objects.all()
    
    if search:
        grupos = grupos.filter(
            Q(codigo__icontains=search) |
            Q(descricao__icontains=search)
        )
    
    context = {'grupos': grupos, 'search': search}
    return render(request, 'gestor/grupo_list.html', context)

@login_required
def grupo_create(request):
    """Criar novo grupo de produto"""
    if request.method == 'POST':
        form = GrupoProdutoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Grupo de produto criado com sucesso!')
            return redirect('gestor:grupo_list')
    else:
        form = GrupoProdutoForm()
    
    context = {'form': form, 'title': 'Novo Grupo de Produto'}
    return render(request, 'gestor/grupo_form.html', context)

@login_required
def grupo_edit(request, pk):
    """Editar grupo de produto"""
    grupo = get_object_or_404(GrupoProduto, codigo=pk)
    
    if request.method == 'POST':
        form = GrupoProdutoForm(request.POST, instance=grupo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Grupo de produto atualizado com sucesso!')
            return redirect('gestor:grupo_list')
    else:
        form = GrupoProdutoForm(instance=grupo)
    
    context = {'form': form, 'title': 'Editar Grupo de Produto', 'grupo': grupo}
    return render(request, 'gestor/grupo_form.html', context)

@login_required
def grupo_delete(request, pk):
    """Deletar grupo de produto"""
    grupo = get_object_or_404(GrupoProduto, codigo=pk)
    
    if request.method == 'POST':
        grupo.delete()
        messages.success(request, 'Grupo de produto excluído com sucesso!')
        return redirect('gestor:grupo_list')
    
    context = {'grupo': grupo}
    return render(request, 'gestor/grupo_confirm_delete.html', context)

# Aliases para compatibilidade com URLs
@login_required
def grupo_produto_list(request):
    """Lista de grupos de produto (alias)"""
    return grupo_list(request)

@login_required
def grupo_produto_create(request):
    """Criar grupo de produto (alias)"""
    return grupo_create(request)

@login_required
def grupo_produto_detail(request, pk):
    """Detalhes do grupo de produto"""
    grupo = get_object_or_404(GrupoProduto, codigo=pk)
    produtos = grupo.produtos.all()[:10]  # Últimos 10 produtos
    
    context = {
        'grupo': grupo,
        'produtos': produtos
    }
    return render(request, 'gestor/grupo_detail.html', context)

@login_required
def grupo_produto_update(request, pk):
    """Editar grupo de produto (alias)"""
    return grupo_edit(request, pk)

@login_required
def grupo_produto_delete(request, pk):
    """Deletar grupo de produto (alias)"""
    return grupo_delete(request, pk)