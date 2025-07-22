# vendedor/views/dashboard.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from datetime import datetime, timedelta

from core.models import Cliente, Vendas, Loja, Vendedor

def vendedor_required(view_func):
    """Decorator para verificar se o usuário é vendedor"""
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if request.user.nivel not in ['vendedor', 'gestor', 'admin']:
            messages.error(request, 'Acesso negado. Apenas vendedores podem acessar esta área.')
            return redirect('login')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@login_required
def home(request):
    """
    Página inicial do Portal do Vendedor
    """
    return render(request, 'vendedor/home.html')

@login_required
@vendedor_required
def dashboard(request):
    """Dashboard do vendedor - versão simplificada"""
    
    # Filtrar apenas clientes do vendedor (se ele tiver código)
    if request.user.codigo_vendedor:
        clientes_vendedor = Cliente.objects.filter(
            codigo_vendedor=request.user.codigo_vendedor,
            status='ativo'  # ✅ CORRIGIDO: usar status='ativo' em vez de ativo=True
        )
    else:
        # Se não tem código, mostrar todos (para gestores/admins)
        clientes_vendedor = Cliente.objects.filter(status='ativo')  # ✅ CORRIGIDO
    
    # Estatísticas básicas
    total_clientes = clientes_vendedor.count()
    
    # Vendas do mês atual (usando model Vendas em vez de RegistroBI)
    mes_atual = datetime.now()
    primeiro_dia_mes = mes_atual.replace(day=1)
    
    try:
        vendas_mes = Vendas.objects.filter(
            data_venda__gte=primeiro_dia_mes,
            cliente__in=clientes_vendedor
        ).aggregate(
            total_vendas=Sum('valor_total'),
            total_quantidade=Sum('quantidade')
        )
    except Exception as e:
        # Se houver erro, usar dados vazios
        vendas_mes = {'total_vendas': 0, 'total_quantidade': 0}
    
    # Clientes mais ativos (com mais registros de venda)
    try:
        clientes_ativos = clientes_vendedor.annotate(
            total_vendas=Count('vendas')  # ✅ CORRIGIDO: 'vendas' em vez de 'vendas_set'
        ).filter(total_vendas__gt=0).order_by('-total_vendas')[:5]
    except:
        clientes_ativos = []
    
    # Últimas consultas realizadas (se o model ConsultaCliente existir)
    try:
        from ..models import ConsultaCliente
        ultimas_consultas = ConsultaCliente.objects.filter(
            vendedor=request.user
        ).select_related('cliente').order_by('-data_consulta')[:10]
    except:
        ultimas_consultas = []
    
    # Vendas recentes
    vendas_recentes = Vendas.objects.filter(
        cliente__in=clientes_vendedor
    ).select_related('cliente', 'produto').order_by('-data_venda')[:10]
    
    context = {
        'total_clientes': total_clientes,
        'vendas_mes': vendas_mes,
        'clientes_ativos': clientes_ativos,
        'ultimas_consultas': ultimas_consultas,
        'vendas_recentes': vendas_recentes,
        'mes_atual': datetime.now().strftime('%B %Y'),
    }
    
    return render(request, 'vendedor/dashboard.html', context)