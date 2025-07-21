# gestor/views/usuario.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from core.models import Usuario
from core.forms import UsuarioForm

@login_required
def usuario_list(request):
    """Lista de usuários"""
    usuarios = Usuario.objects.all().order_by('username')
    
    # Adicionar contagem de vendedores para cada usuário
    for usuario in usuarios:
        usuario.count_vendedores = usuario.total_vendedores_permitidos
    
    context = {
        'usuarios': usuarios
    }
    return render(request, 'gestor/usuario_list.html', context)

@login_required
def usuario_create(request):
    """Criar usuário"""
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            messages.success(
                request, 
                f'Usuário "{usuario.username}" criado com sucesso! '
                f'Acesso a {usuario.total_vendedores_permitidos} vendedores.'
            )
            return redirect('gestor:usuario_list')
    else:
        form = UsuarioForm()
    
    context = {
        'form': form,
        'title': 'Novo Usuário'
    }
    return render(request, 'gestor/usuario_form.html', context)

@login_required
def usuario_detail(request, pk):
    """Detalhes do usuário"""
    usuario = get_object_or_404(Usuario, pk=pk)
    
    # Buscar vendedores permitidos
    vendedores_permitidos = usuario.get_vendedores_permitidos()[:10]  # Primeiros 10
    
    # Estatísticas
    total_vendedores_sistema = Usuario.objects.first().get_vendedores_permitidos().count() if Usuario.objects.exists() else 0
    vendedores_com_acesso = usuario.total_vendedores_permitidos
    
    context = {
        'usuario': usuario,
        'vendedores_permitidos': vendedores_permitidos,
        'total_vendedores_sistema': total_vendedores_sistema,
        'vendedores_com_acesso': vendedores_com_acesso,
    }
    return render(request, 'gestor/usuario_detail.html', context)

@login_required
def usuario_update(request, pk):
    """Editar usuário"""
    usuario = get_object_or_404(Usuario, pk=pk)
    
    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            usuario = form.save()
            messages.success(
                request, 
                f'Usuário "{usuario.username}" atualizado com sucesso! '
                f'Acesso a {usuario.total_vendedores_permitidos} vendedores.'
            )
            return redirect('gestor:usuario_list')
    else:
        form = UsuarioForm(instance=usuario)
    
    context = {
        'form': form,
        'usuario': usuario,
        'title': f'Editar Usuário - {usuario.username}'
    }
    return render(request, 'gestor/usuario_form.html', context)

@login_required
def usuario_delete(request, pk):
    """Deletar usuário"""
    usuario = get_object_or_404(Usuario, pk=pk)
    
    if request.method == 'POST':
        username = usuario.username
        usuario.delete()
        messages.success(request, f'Usuário "{username}" excluído com sucesso!')
        return redirect('gestor:usuario_list')
    
    context = {
        'usuario': usuario
    }
    return render(request, 'gestor/usuario_confirm_delete.html', context)