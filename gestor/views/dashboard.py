# gestor/views/dashboard.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.models import Cliente, Produto, Vendas, Loja

@login_required
def home(request):
    """
    Página inicial do Portal do Gestor
    """
    return render(request, 'gestor/home.html')

@login_required
def dashboard(request):
    """View para o dashboard do gestor"""
    context = {
        'total_clientes': Cliente.objects.count(),
        'total_produtos': Produto.objects.count(),
        'total_vendas': Vendas.objects.count(),
        'total_lojas': Loja.objects.count(),
    }
    return render(request, 'gestor/dashboard.html', context)