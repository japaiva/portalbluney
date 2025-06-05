# gestor/views/cliente_contato.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from core.models import Cliente, ClienteContato
from core.forms import ClienteContatoForm

@login_required
def cliente_contato_create(request, cliente_id):
    """Criar novo contato para o cliente"""
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    
    if request.method == 'POST':
        form = ClienteContatoForm(request.POST)
        if form.is_valid():
            contato = form.save(commit=False)
            contato.cliente = cliente
            
            # Define o código master (do cliente ou o próprio código se for cliente principal)
            if cliente.codigo_master:
                contato.codigo_master = cliente.codigo_master
            else:
                contato.codigo_master = cliente.codigo
            
            # Define o código do contato igual ao do cliente
            contato.codigo = cliente.codigo
            
            # Se este contato está marcado como principal, remover esta marca de outros
            if contato.principal:
                cliente.contatos.filter(principal=True).update(principal=False)
            
            contato.save()
            messages.success(request, 'Contato adicionado com sucesso.')
            return redirect('gestor:cliente_detail', pk=cliente.id)
    else:
        # Inicializar com valores padrão
        initial_data = {
            'codigo': cliente.codigo,
            'codigo_master': cliente.codigo_master or cliente.codigo,
        }
        form = ClienteContatoForm(initial=initial_data)
    
    return render(request, 'gestor/cliente_contato_form.html', {
        'form': form, 
        'cliente': cliente
    })

@login_required
def cliente_contato_update(request, pk):
    """Atualizar contato do cliente"""
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
    """Deletar contato do cliente"""
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