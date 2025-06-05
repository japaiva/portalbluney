# gestor/views/sincronizacao.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def sincronizacao_dashboard(request):
    """Dashboard de sincronização"""
    context = {
        'title': 'Sincronização de Dados'
    }
    return render(request, 'gestor/sincronizacao_dashboard.html', context)

@login_required
def sincronizar_bi(request):
    """View para sincronizar dados do BI"""
    # Esta view pode ser expandida conforme necessário
    messages.info(request, 'Funcionalidade de sincronização BI em desenvolvimento')
    return redirect('gestor:sincronizacao_dashboard')

@login_required
def sincronizar_receita(request):
    """View para sincronizar dados da Receita Federal"""
    # Esta view pode ser expandida conforme necessário
    messages.info(request, 'Funcionalidade de sincronização Receita Federal em desenvolvimento')
    return redirect('gestor:sincronizacao_dashboard')

@login_required
def sincronizacao_completa(request):
    """View para sincronização completa"""
    # Esta view pode ser expandida conforme necessário
    messages.info(request, 'Funcionalidade de sincronização completa em desenvolvimento')
    return redirect('gestor:sincronizacao_dashboard')