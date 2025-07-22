# vendedor/views/cliente.py - VERSÃO COMPLETA COM TODAS AS APIS

import logging
from datetime import timedelta, datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Sum, Prefetch
from django.utils import timezone
from django.http import JsonResponse

from core.models import Cliente, ClienteContato, Vendas, Loja, Vendedor

logger = logging.getLogger(__name__)

@login_required
def cliente_list(request):
    """Lista de clientes com filtros - SOMENTE LEITURA"""
    # Filtro por tipo de cliente
    tipo_cliente = request.GET.get('tipo', 'principal')
    if tipo_cliente == 'principal':
        clientes_list = Cliente.objects.filter(
            Q(codigo_master__isnull=True) | Q(codigo_master='')
        )
    elif tipo_cliente == 'coligados':
        clientes_list = Cliente.objects.filter(
            codigo_master__isnull=False
        ).exclude(codigo_master='')
    else:
        clientes_list = Cliente.objects.all()
    
    # Filtro por status
    status = request.GET.get('status', 'ativo')
    if status == 'ativo':
        clientes_list = clientes_list.filter(status='ativo')
    elif status == 'inativo':
        clientes_list = clientes_list.filter(status='inativo')
    elif status == 'rascunho':
        clientes_list = clientes_list.filter(status='rascunho')
    elif status == 'outros':
        clientes_list = clientes_list.filter(status='outros')
    
    # *** CONTROLE DE ACESSO: Vendedor vê apenas seus clientes ***
    if request.user.nivel == 'vendedor' and request.user.codigo_vendedor:
        clientes_list = clientes_list.filter(codigo_vendedor=request.user.codigo_vendedor)
    
    # Filtro manual por vendedor (para gestores/admins)
    vendedor_codigo = request.GET.get('vendedor', '')
    if vendedor_codigo and request.user.nivel in ['admin', 'gestor']:
        clientes_list = clientes_list.filter(codigo_vendedor=vendedor_codigo)
    
    # Filtro por loja
    loja_codigo = request.GET.get('loja', '')
    if loja_codigo:
        clientes_list = clientes_list.filter(codigo_loja=loja_codigo)
    
    # Busca
    query = request.GET.get('q', '')
    if query:
        clientes_list = clientes_list.filter(
            Q(nome__icontains=query) | 
            Q(codigo__icontains=query) |
            Q(cpf_cnpj__icontains=query) |
            Q(nome_razao_social__icontains=query)
        )
    
    clientes_list = clientes_list.order_by('nome')
    
    # Paginação
    paginator = Paginator(clientes_list, 15)
    page = request.GET.get('page', 1)
    
    try:
        clientes = paginator.page(page)
    except PageNotAnInteger:
        clientes = paginator.page(1)
    except EmptyPage:
        clientes = paginator.page(paginator.num_pages)
    
    # Buscar dados para os selects (apenas se for gestor/admin)
    if request.user.nivel in ['admin', 'gestor']:
        lojas = Loja.objects.filter(ativo=True).order_by('codigo')
        vendedores = Vendedor.objects.filter(ativo=True).order_by('codigo')
    else:
        lojas = []
        vendedores = []
    
    context = {
        'clientes': clientes, 
        'status_filtro': status,
        'tipo_filtro': tipo_cliente,
        'vendedor_filtro': vendedor_codigo,
        'loja_filtro': loja_codigo,
        'query': query,
        'lojas': lojas,
        'vendedores': vendedores,
        'is_readonly': True,  # Indica que é somente leitura
    }
    
    return render(request, 'vendedor/cliente_list.html', context)

@login_required
def cliente_detail(request, pk):
    """Detalhe do cliente - SOMENTE VISUALIZAÇÃO"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    # *** CONTROLE DE ACESSO: Verificar se vendedor pode ver este cliente ***
    if request.user.nivel == 'vendedor' and request.user.codigo_vendedor:
        if cliente.codigo_vendedor != request.user.codigo_vendedor:
            messages.error(request, 'Você só pode visualizar clientes do seu código de vendedor.')
            return redirect('vendedor:cliente_list')
    
    contatos = cliente.contatos.all()
    
    # Buscar cliente master (se houver)
    cliente_master = None
    if cliente.codigo_master:
        cliente_master = Cliente.objects.filter(codigo=cliente.codigo_master).first()
    
    # Buscar clientes associados (sub-clientes)
    clientes_associados = Cliente.objects.filter(codigo_master=cliente.codigo).order_by('nome')
    
    # Buscar contatos de sub-clientes
    contatos_sub_clientes = []
    if clientes_associados:
        contatos_sub_clientes = ClienteContato.objects.filter(
            cliente__in=clientes_associados
        ).select_related('cliente').order_by('cliente__nome', '-principal', 'nome')
    
    # Todos os contatos (principal + sub-clientes)
    todos_contatos = list(contatos) + list(contatos_sub_clientes)
    
    # Obter dados de vendas recentes (últimos 90 dias)
    hoje = timezone.now().date()
    data_inicio = hoje - timedelta(days=90)
    
    # Obter códigos de todos os clientes (principal + associados)
    codigos_clientes = [cliente.codigo]
    if not cliente.codigo_master and clientes_associados:
        codigos_clientes.extend([c.codigo for c in clientes_associados])
    
    # Buscar vendas recentes
    vendas_recentes = []
    total_vendas_recentes = 0
    
    try:
        vendas_recentes = Vendas.objects.filter(
            cliente__codigo__in=codigos_clientes,
            data_venda__gte=data_inicio
        ).order_by('-data_venda')[:10]
        
        total_vendas_recentes = Vendas.objects.filter(
            cliente__codigo__in=codigos_clientes,
            data_venda__gte=data_inicio
        ).aggregate(total=Sum('valor_total'))['total'] or 0
    except Exception as e:
        logger.warning(f"Erro ao buscar dados de vendas: {e}")
    
    context = {
        'cliente': cliente,
        'cliente_master': cliente_master,
        'contatos': contatos,
        'contatos_sub_clientes': contatos_sub_clientes,
        'todos_contatos': todos_contatos,
        'clientes_associados': clientes_associados,
        'vendas_recentes': vendas_recentes,
        'total_vendas_recentes': total_vendas_recentes,
        'is_readonly': True,  # Indica que é somente leitura
        'vendedor_info': {
            'codigo': cliente.codigo_vendedor,
            'nome': getattr(cliente, 'nome_vendedor', '') or '',
        }
    }
    
    return render(request, 'vendedor/cliente_detail.html', context)

@login_required
def cliente_detail_by_codigo(request, codigo):
    """View para acessar cliente pelo código - SOMENTE VISUALIZAÇÃO"""
    cliente = get_object_or_404(Cliente, codigo=codigo)
    
    # *** CONTROLE DE ACESSO: Verificar se vendedor pode ver este cliente ***
    if request.user.nivel == 'vendedor' and request.user.codigo_vendedor:
        if cliente.codigo_vendedor != request.user.codigo_vendedor:
            messages.error(request, 'Você só pode visualizar clientes do seu código de vendedor.')
            return redirect('vendedor:cliente_list')
    
    return redirect('vendedor:cliente_detail', pk=cliente.id)

# ===== APIs PARA AJAX (ADAPTADAS DO GESTOR) =====

@login_required
def api_vendedor_por_codigo(request, codigo):
    """API para buscar vendedor por código - AJAX"""
    try:
        # Normalizar código para 3 dígitos
        codigo_formatado = str(codigo).zfill(3)
        
        # Buscar vendedor
        vendedor = Vendedor.objects.select_related('loja').get(
            codigo=codigo_formatado, 
            ativo=True
        )
        
        return JsonResponse({
            'success': True,
            'codigo': vendedor.codigo,
            'nome': vendedor.nome,
            'email': vendedor.email or '',
            'telefone': vendedor.telefone or '',
            'loja': f"{vendedor.loja.codigo} - {vendedor.loja.nome}" if vendedor.loja else '',
            'loja_codigo': vendedor.loja.codigo if vendedor.loja else '',
            'loja_nome': vendedor.loja.nome if vendedor.loja else '',
        })
        
    except Vendedor.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': f'Vendedor com código {codigo} não encontrado ou inativo'
        })
    except Exception as e:
        logger.error(f"Erro na API vendedor_por_codigo: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Erro interno do servidor'
        })

@login_required
def api_cliente_por_codigo(request, codigo):
    """API para buscar cliente por código - AJAX"""
    try:
        cliente = Cliente.objects.get(codigo=codigo)
        
        # *** CONTROLE DE ACESSO: Verificar se vendedor pode ver este cliente ***
        if request.user.nivel == 'vendedor' and request.user.codigo_vendedor:
            if cliente.codigo_vendedor != request.user.codigo_vendedor:
                return JsonResponse({
                    'success': False,
                    'message': 'Cliente não encontrado ou sem permissão para visualizar'
                })
        
        return JsonResponse({
            'success': True,
            'codigo': cliente.codigo,
            'nome': cliente.nome,
            'status': cliente.get_status_display(),
            'nome_fantasia': cliente.nome_fantasia or '',
            'cpf_cnpj': cliente.cpf_cnpj or '',
        })
        
    except Cliente.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': f'Cliente com código {codigo} não encontrado'
        })
    except Exception as e:
        logger.error(f"Erro na API cliente_por_codigo: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Erro interno do servidor'
        })

@login_required  
def api_consultar_receita(request, cpf_cnpj):
    """API para consultar dados na Receita Federal - DESABILITADA NO VENDEDOR"""
    return JsonResponse({
        'success': False,
        'message': 'Consulta à Receita Federal não disponível no módulo vendedor. Entre em contato com o gestor.'
    })

# ===== CONSULTA BI (ADAPTADA DO GESTOR) =====

@login_required
def consultar_bi(request, codigo):
    """
    View para consultar dados de BI (vendas) do cliente - ADAPTADA PARA VENDEDOR
    """
    cliente = get_object_or_404(Cliente, codigo=codigo)
    
    # *** CONTROLE DE ACESSO: Verificar se vendedor pode ver este cliente ***
    if request.user.nivel == 'vendedor' and request.user.codigo_vendedor:
        if cliente.codigo_vendedor != request.user.codigo_vendedor:
            messages.error(request, 'Você só pode visualizar dados de BI de seus clientes.')
            return redirect('vendedor:cliente_list')
    
    # Parâmetros de filtro
    filtro_periodo = request.GET.get('periodo', '90')  # Default: últimos 90 dias
    data_inicio_param = request.GET.get('data_inicio')
    data_fim_param = request.GET.get('data_fim')
    
    # Definir datas
    hoje = timezone.now().date()
    
    if filtro_periodo == 'custom' and data_inicio_param and data_fim_param:
        try:
            data_inicio = datetime.strptime(data_inicio_param, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim_param, '%Y-%m-%d').date()
        except ValueError:
            # Fallback para últimos 90 dias se datas inválidas
            data_inicio = hoje - timedelta(days=90)
            data_fim = hoje
            filtro_periodo = '90'
    else:
        # Período padrão baseado na escolha
        if filtro_periodo == '30':
            data_inicio = hoje - timedelta(days=30)
        elif filtro_periodo == '180':
            data_inicio = hoje - timedelta(days=180)
        elif filtro_periodo == '365':
            data_inicio = hoje - timedelta(days=365)
        else:  # default: 90 dias
            data_inicio = hoje - timedelta(days=90)
            filtro_periodo = '90'
        
        data_fim = hoje
    
    # Obter códigos de todos os clientes (principal + associados)
    codigos_clientes = [cliente.codigo]
    if not cliente.codigo_master:
        # Se é cliente principal, incluir sub-clientes
        sub_clientes = Cliente.objects.filter(codigo_master=cliente.codigo)
        if sub_clientes:
            codigos_clientes.extend([c.codigo for c in sub_clientes])
    
    # Buscar vendas no período
    try:
        vendas = Vendas.objects.filter(
            cliente__codigo__in=codigos_clientes,
            data_venda__gte=data_inicio,
            data_venda__lte=data_fim
        ).select_related(
            'produto', 'loja', 'grupo_produto', 'fabricante', 'cliente'
        ).order_by('-data_venda')
        
        # Calcular totais
        totais = vendas.aggregate(
            total_valor=Sum('valor_total'),
            total_quantidade=Sum('quantidade')
        )
        
        total_valor = totais['total_valor'] or 0
        total_quantidade = totais['total_quantidade'] or 0
        
        # Limitar vendas para exibição (máximo 500 registros para vendedor)
        vendas_limitadas = vendas[:500] if vendas.count() > 500 else vendas
        
    except Exception as e:
        logger.error(f"Erro ao consultar dados de BI para cliente {codigo}: {str(e)}")
        vendas = Vendas.objects.none()
        vendas_limitadas = vendas
        total_valor = 0
        total_quantidade = 0
    
    context = {
        'cliente': cliente,
        'vendas': vendas_limitadas,
        'total_valor': total_valor,
        'total_quantidade': total_quantidade,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'filtro_periodo': filtro_periodo,
        'total_registros': vendas.count(),
        'registros_limitados': vendas.count() > 500,
        'is_readonly': True,  # Indica que é somente leitura
    }
    
    return render(request, 'vendedor/cliente_bi.html', context)