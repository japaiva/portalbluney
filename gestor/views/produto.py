# gestor/views/produto.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from core.models import Produto, Vendas
from core.forms import ProdutoForm

@login_required
def produto_list(request):
    """Lista de produtos"""
    search = request.GET.get('search', '')
    produtos = Produto.objects.select_related('grupo', 'fabricante').all()
    
    if search:
        produtos = produtos.filter(
            Q(codigo__icontains=search) |
            Q(descricao__icontains=search) |
            Q(grupo__descricao__icontains=search) |
            Q(fabricante__descricao__icontains=search)
        )
    
    paginator = Paginator(produtos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'page_obj': page_obj, 'search': search}
    return render(request, 'gestor/produto_list.html', context)

@login_required
def produto_create(request):
    """Criar novo produto"""
    if request.method == 'POST':
        form = ProdutoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Produto criado com sucesso!')
            return redirect('gestor:produto_list')
    else:
        form = ProdutoForm()
    
    context = {'form': form, 'title': 'Novo Produto'}
    return render(request, 'gestor/produto_form.html', context)

@login_required
def produto_edit(request, pk):
    """Editar produto"""
    produto = get_object_or_404(Produto, codigo=pk)
    
    if request.method == 'POST':
        form = ProdutoForm(request.POST, instance=produto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Produto atualizado com sucesso!')
            return redirect('gestor:produto_list')
    else:
        form = ProdutoForm(instance=produto)
    
    context = {'form': form, 'title': 'Editar Produto', 'produto': produto}
    return render(request, 'gestor/produto_form.html', context)

@login_required
def produto_delete(request, pk):
    """Deletar produto"""
    produto = get_object_or_404(Produto, codigo=pk)
    
    if request.method == 'POST':
        produto.delete()
        messages.success(request, 'Produto excluído com sucesso!')
        return redirect('gestor:produto_list')
    
    context = {'produto': produto}
    return render(request, 'gestor/produto_confirm_delete.html', context)

@login_required
def produto_detail(request, pk):
    """Detalhes do produto"""
    produto = get_object_or_404(Produto, codigo=pk)
    
    # Buscar vendas recentes deste produto
    vendas_recentes = Vendas.objects.filter(produto=produto).order_by('-data_venda')[:10]
    
    context = {
        'produto': produto,
        'vendas_recentes': vendas_recentes
    }
    return render(request, 'gestor/produto_detail.html', context)

@login_required
def produto_update(request, pk):
    """View para editar produto (alias para produto_edit)"""
    return produto_edit(request, pk)