# gestor/views/cliente.py

import logging
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Sum, Prefetch
from django.utils import timezone
from django.db import transaction

from core.models import Cliente, ClienteContato, ClienteCnaeSecundario, Vendas
from core.forms import ClienteForm, ClienteCnaeSecundarioFormSet

logger = logging.getLogger(__name__)

@login_required
def cliente_list(request):
    """Lista de clientes com filtros múltiplos"""
    # Filtro por tipo de cliente (principal/sub-cliente)
    tipo_cliente = request.GET.get('tipo', 'todos')
    if tipo_cliente == 'principal':
        clientes_list = Cliente.objects.filter(
            Q(codigo_master__isnull=True) | Q(codigo_master='')
        )
    elif tipo_cliente == 'coligados':
        clientes_list = Cliente.objects.filter(
            codigo_master__isnull=False
        ).exclude(codigo_master='')
    else:  # todos
        clientes_list = Cliente.objects.all()
    
    # Filtro por status
    status = request.GET.get('status', 'todos')
    if status == 'ativo':
        clientes_list = clientes_list.filter(status='ativo')
    elif status == 'inativo':
        clientes_list = clientes_list.filter(status='inativo')
    elif status == 'rascunho':
        clientes_list = clientes_list.filter(status='rascunho')
    # Se 'todos', não aplica filtro
    
    # Busca por nome, código ou CPF/CNPJ
    query = request.GET.get('q')
    if query:
        clientes_list = clientes_list.filter(
            Q(nome__icontains=query) | 
            Q(codigo__icontains=query) |
            Q(cpf_cnpj__icontains=query) |
            Q(nome_razao_social__icontains=query)
        )
    
    # Prefetch para otimizar CNAEs secundários
    clientes_list = clientes_list.prefetch_related(
        Prefetch('cnaes_secundarios', queryset=ClienteCnaeSecundario.objects.order_by('ordem'))
    ).order_by('nome')
    
    # Paginação
    paginator = Paginator(clientes_list, 15)  # 15 por página
    page = request.GET.get('page', 1)
    
    try:
        clientes = paginator.page(page)
    except PageNotAnInteger:
        clientes = paginator.page(1)
    except EmptyPage:
        clientes = paginator.page(paginator.num_pages)
    
    context = {
        'clientes': clientes, 
        'status_filtro': status,
        'tipo_filtro': tipo_cliente,
        'query': query
    }
    
    return render(request, 'gestor/cliente_list.html', context)

@login_required
def cliente_create(request):
    """Criar novo cliente"""
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        cnaes_formset = ClienteCnaeSecundarioFormSet(
            request.POST, 
            prefix='cnaes'
        )
        
        if form.is_valid() and cnaes_formset.is_valid():
            try:
                with transaction.atomic():
                    # Salvar cliente
                    cliente = form.save()
                    
                    # Salvar CNAEs secundários
                    cnaes_formset.instance = cliente
                    cnaes_formset.save()
                    
                    # Contar CNAEs salvos
                    cnaes_count = cliente.cnaes_secundarios.count()
                    if cnaes_count > 0:
                        messages.success(request, 
                            f'Cliente "{cliente.nome}" cadastrado com sucesso! '
                            f'CNAE principal + {cnaes_count} CNAEs secundários salvos.'
                        )
                    else:
                        messages.success(request, f'Cliente "{cliente.nome}" cadastrado com sucesso.')
                    
                    return redirect('gestor:cliente_detail', pk=cliente.id)
                    
            except Exception as e:
                logger.error(f"Erro ao salvar cliente com CNAEs: {str(e)}")
                messages.error(request, f"Erro ao salvar: {str(e)}")
        else:
            messages.error(request, "Corrija os erros abaixo")
    else:
        # Verificar se é um sub-cliente sendo criado
        codigo_master = request.GET.get('codigo_master', '')
        initial_data = {}
        cliente_master = None
        
        if codigo_master:
            initial_data = {'codigo_master': codigo_master}
            cliente_master = Cliente.objects.filter(codigo=codigo_master).first()
        
        form = ClienteForm(initial=initial_data)
        cnaes_formset = ClienteCnaeSecundarioFormSet(
            prefix='cnaes'
        )
    
    context = {
        'form': form,
        'cnaes_formset': cnaes_formset,
        'cliente_master_nome': cliente_master.nome if cliente_master else None
    }
    
    return render(request, 'gestor/cliente_form.html', context)

@login_required
def cliente_update(request, pk):
    """Atualizar cliente existente"""
    cliente = get_object_or_404(Cliente, pk=pk)
    cliente_master = None
    
    if cliente.codigo_master:
        cliente_master = Cliente.objects.filter(codigo=cliente.codigo_master).first()
    
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        cnaes_formset = ClienteCnaeSecundarioFormSet(
            request.POST, 
            instance=cliente,
            prefix='cnaes'
        )
        
        if form.is_valid() and cnaes_formset.is_valid():
            try:
                with transaction.atomic():
                    # Salvar cliente
                    cliente = form.save()
                    
                    # Salvar CNAEs secundários
                    cnaes_formset.save()
                    
                    # Contar CNAEs salvos
                    cnaes_count = cliente.cnaes_secundarios.count()
                    if cnaes_count > 0:
                        messages.success(request, 
                            f'Cliente "{cliente.nome}" atualizado com sucesso! '
                            f'CNAE principal + {cnaes_count} CNAEs secundários salvos.'
                        )
                    else:
                        messages.success(request, f'Cliente "{cliente.nome}" atualizado com sucesso.')
                    
                    return redirect('gestor:cliente_detail', pk=cliente.id)
                    
            except Exception as e:
                logger.error(f"Erro ao atualizar cliente com CNAEs: {str(e)}")
                messages.error(request, f"Erro ao atualizar: {str(e)}")
        else:
            messages.error(request, "Corrija os erros abaixo")
    else:
        form = ClienteForm(instance=cliente)
        cnaes_formset = ClienteCnaeSecundarioFormSet(
            instance=cliente,
            prefix='cnaes'
        )
    
    context = {
        'form': form, 
        'cnaes_formset': cnaes_formset,
        'cliente': cliente,
        'cliente_master_nome': cliente_master.nome if cliente_master else None
    }
    
    return render(request, 'gestor/cliente_form.html', context)

@login_required
def cliente_delete(request, pk):
    """Deletar cliente"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        cliente_nome = cliente.nome  # Get name before deleting
        cliente.delete()
        messages.success(request, f'Cliente "{cliente_nome}" excluído com sucesso.')
        return redirect('gestor:cliente_list')
    
    return render(request, 'gestor/cliente_confirm_delete.html', {
        'cliente': cliente
    })

@login_required
def cliente_detail(request, pk):
    """Detalhe do cliente"""
    cliente = get_object_or_404(Cliente, pk=pk)
    contatos = cliente.contatos.all()
    
    # Buscar CNAEs secundários
    cnaes_secundarios = cliente.cnaes_secundarios.all().order_by('ordem')
    
    # Buscar cliente master (se houver)
    cliente_master = None
    if cliente.codigo_master:
        cliente_master = Cliente.objects.filter(codigo=cliente.codigo_master).first()
    
    # Buscar clientes associados (sub-clientes)
    clientes_associados = Cliente.objects.filter(codigo_master=cliente.codigo).order_by('nome')
    
    # Obter todos os contatos (incluindo sub-clientes)
    todos_contatos = list(contatos)
    
    # Obter contatos dos sub-clientes se for cliente principal
    contatos_sub_clientes = []
    if not cliente.codigo_master and clientes_associados:
        sub_clientes_ids = [c.id for c in clientes_associados]
        contatos_sub_clientes = list(ClienteContato.objects.filter(
            cliente_id__in=sub_clientes_ids
        ).order_by('cliente__nome', '-principal', 'nome'))
        todos_contatos.extend(contatos_sub_clientes)
    
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
        # Buscar vendas recentes
        vendas_recentes = Vendas.objects.filter(
            cliente__codigo__in=codigos_clientes,
            data_venda__gte=data_inicio
        ).order_by('-data_venda')[:10]
        
        # Calcular total de vendas no período
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
        'cnaes_secundarios': cnaes_secundarios,
        'clientes_associados': clientes_associados,
        'contatos_sub_clientes': contatos_sub_clientes,
        'todos_contatos': todos_contatos,
        'vendas_recentes': vendas_recentes,
        'total_vendas_recentes': total_vendas_recentes
    }
    
    return render(request, 'gestor/cliente_detail.html', context)

@login_required
def cliente_detail_by_codigo(request, codigo):
    """View para acessar cliente pelo código"""
    cliente = get_object_or_404(Cliente, codigo=codigo)
    return redirect('gestor:cliente_detail', pk=cliente.id)