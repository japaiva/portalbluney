# vendedor/views/vendas.py - VERSÃO CORRIGIDA COM CONTROLE DE ACESSO

import logging
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from core.models import Vendas, Loja, Vendedor
from core.forms import VendasForm

logger = logging.getLogger(__name__)

@login_required
def vendas_list(request):
    """Lista de vendas com filtros - COM CONTROLE DE ACESSO CORRIGIDO"""
    
    # ===== CONTROLE DE ACESSO INICIAL =====
    if request.user.nivel == 'vendedor':
        # Para vendedores, verificar se tem vendedores configurados
        codigos_permitidos = request.user.get_codigos_vendedores_permitidos()
        
        if not codigos_permitidos:
            messages.warning(request, 'Você não tem vendedores configurados para visualização. Entre em contato com o administrador.')
            # Retornar queryset vazio
            vendas_list = Vendas.objects.none()
            lojas_disponiveis = Loja.objects.none()
            vendedores_disponiveis = Vendedor.objects.none()
            
            context = {
                'vendas': vendas_list,
                'search': '',
                'data_inicio': '',
                'data_fim': '',
                'loja_filtro': '',
                'vendedor_filtro': '',
                'lojas_disponiveis': lojas_disponiveis,
                'vendedores_disponiveis': vendedores_disponiveis,
                'total_quantidade': 0,
                'total_valor': 0,
                'is_vendedor_sem_acesso': True,
            }
            return render(request, 'vendedor/vendas_list.html', context)
    
    # ===== FILTROS MÚLTIPLOS =====
    search = request.GET.get('search', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    loja_filtro = request.GET.get('loja', '')
    vendedor_filtro = request.GET.get('vendedor', '')
    
    # *** CONTROLE DE ACESSO PARA VENDEDORES ***
    if request.user.nivel == 'vendedor':
        codigos_permitidos = request.user.get_codigos_vendedores_permitidos()
        
        # Verificar se vendedor tentou filtrar por vendedor não permitido
        if vendedor_filtro and vendedor_filtro not in codigos_permitidos:
            messages.warning(request, f'Você não tem permissão para visualizar dados do vendedor {vendedor_filtro}.')
            vendedor_filtro = ''  # Ignorar o filtro
        
        # Se não especificou vendedor, usar todos os permitidos
        if not vendedor_filtro:
            vendedores_filtro_list = codigos_permitidos
        else:
            vendedores_filtro_list = [vendedor_filtro]
    else:
        # *** GESTORES/ADMINS: FILTRO NORMAL ***
        if vendedor_filtro:
            vendedores_filtro_list = [vendedor_filtro]
        else:
            vendedores_filtro_list = None  # Todos os vendedores
    
    # ===== QUERY BASE COM CONTROLE DE ACESSO =====
    vendas_list = Vendas.objects.select_related(
        'cliente', 'produto', 'produto__grupo', 'produto__fabricante', 'loja'
    ).all()
    
    # *** APLICAR FILTRO DE VENDEDORES PERMITIDOS PRIMEIRO ***
    if request.user.nivel == 'vendedor':
        # Filtrar por vendedores permitidos
        vendas_list = vendas_list.filter(cliente__codigo_vendedor__in=vendedores_filtro_list)
    elif vendedores_filtro_list:
        # Para gestores/admins, aplicar filtro se especificado
        vendas_list = vendas_list.filter(cliente__codigo_vendedor__in=vendedores_filtro_list)
    
    # ===== APLICAR OUTROS FILTROS =====
    if search:
        vendas_list = vendas_list.filter(
            Q(cliente__nome__icontains=search) |
            Q(cliente__codigo__icontains=search) |
            Q(produto__descricao__icontains=search) |
            Q(produto__codigo__icontains=search) |
            Q(numero_nf__icontains=search)
        )
    
    if data_inicio:
        try:
            data_inicio_parsed = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            vendas_list = vendas_list.filter(data_venda__gte=data_inicio_parsed)
        except ValueError:
            messages.warning(request, 'Data de início inválida.')
    
    if data_fim:
        try:
            data_fim_parsed = datetime.strptime(data_fim, '%Y-%m-%d').date()
            vendas_list = vendas_list.filter(data_venda__lte=data_fim_parsed)
        except ValueError:
            messages.warning(request, 'Data de fim inválida.')
    
    if loja_filtro:
        vendas_list = vendas_list.filter(loja__codigo=loja_filtro)
    
    # ===== ORDENAÇÃO =====
    vendas_list = vendas_list.order_by('-data_venda', '-id')
    
    # ===== PAGINAÇÃO =====
    paginator = Paginator(vendas_list, 20)
    page = request.GET.get('page', 1)
    
    try:
        vendas = paginator.page(page)
    except PageNotAnInteger:
        vendas = paginator.page(1)
    except EmptyPage:
        vendas = paginator.page(paginator.num_pages)
    
    # ===== DADOS PARA FILTROS COM CONTROLE DE ACESSO =====
    lojas_disponiveis = Loja.objects.filter(ativo=True).order_by('codigo')
    
    # *** VENDEDORES: DIFERENTE PARA CADA NÍVEL ***
    if request.user.nivel == 'vendedor':
        # Vendedores veem apenas os permitidos
        vendedores_disponiveis = request.user.get_vendedores_permitidos()
        vendedor_filtro_desabilitado = True
        
        # Se só tem um vendedor permitido, forçar seleção
        if vendedores_disponiveis.count() == 1:
            vendedor_unico = vendedores_disponiveis.first()
            if not vendedor_filtro:
                vendedor_filtro = vendedor_unico.codigo
    else:
        # Gestores/admins veem todos
        vendedores_disponiveis = Vendedor.objects.filter(ativo=True).order_by('nome')
        vendedor_filtro_desabilitado = False
    
    # ===== CALCULAR TOTAIS DA PÁGINA ATUAL =====
    total_quantidade = sum(v.quantidade for v in vendas)
    total_valor = sum(v.valor_total for v in vendas)
    
    context = {
        'vendas': vendas,
        'search': search,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'loja_filtro': loja_filtro,
        'vendedor_filtro': vendedor_filtro,
        'lojas_disponiveis': lojas_disponiveis,
        'vendedores_disponiveis': vendedores_disponiveis,
        'total_quantidade': total_quantidade,
        'total_valor': total_valor,
        
        # *** INFORMAÇÕES DE CONTROLE DE ACESSO ***
        'vendedor_filtro_desabilitado': vendedor_filtro_desabilitado if request.user.nivel == 'vendedor' else False,
        'total_vendedores_permitidos': request.user.total_vendedores_permitidos if request.user.nivel == 'vendedor' else 'Todos',
        'is_vendedor_restrito': request.user.nivel == 'vendedor',
        'vendedores_permitidos_info': {
            'total': vendedores_disponiveis.count(),
            'codigos': list(vendedores_disponiveis.values_list('codigo', flat=True)) if request.user.nivel == 'vendedor' else None
        } if request.user.nivel == 'vendedor' else None,
    }
    
    return render(request, 'vendedor/vendas_list.html', context)

@login_required
def vendas_create(request):
    """Criar nova venda - COM CONTROLE DE ACESSO"""
    
    # *** VERIFICAR SE VENDEDOR TEM PERMISSÃO PARA CRIAR VENDAS ***
    if request.user.nivel == 'vendedor':
        codigos_permitidos = request.user.get_codigos_vendedores_permitidos()
        if not codigos_permitidos:
            messages.error(request, 'Você não tem permissão para criar vendas. Entre em contato com o administrador.')
            return redirect('vendedor:vendas_list')
    
    if request.method == 'POST':
        form = VendasForm(request.POST)
        if form.is_valid():
            try:
                venda = form.save()
                
                # *** VERIFICAR SE VENDEDOR PODE VER A VENDA CRIADA ***
                if request.user.nivel == 'vendedor':
                    if not request.user.pode_visualizar_vendedor(venda.cliente.codigo_vendedor):
                        messages.warning(request, f'Venda criada, mas você não tem permissão para visualizar dados do vendedor {venda.cliente.codigo_vendedor}.')
                        return redirect('vendedor:vendas_list')
                
                messages.success(request, f'Venda para {venda.cliente.nome} criada com sucesso!')
                return redirect('vendedor:vendas_list')
            except Exception as e:
                logger.error(f"Erro ao criar venda: {str(e)}")
                messages.error(request, f'Erro ao criar venda: {str(e)}')
        else:
            messages.error(request, 'Corrija os erros abaixo.')
    else:
        form = VendasForm()
    
    context = {
        'form': form, 
        'title': 'Nova Venda',
        'is_create': True,
        'is_vendedor_restrito': request.user.nivel == 'vendedor',
    }
    return render(request, 'vendedor/vendas_form.html', context)

@login_required
def vendas_edit(request, pk):
    """Editar venda - COM CONTROLE DE ACESSO"""
    venda = get_object_or_404(Vendas, pk=pk)
    
    # *** CONTROLE DE ACESSO: Verificar se vendedor pode ver esta venda ***
    if request.user.nivel == 'vendedor':
        if not request.user.pode_visualizar_vendedor(venda.cliente.codigo_vendedor):
            messages.error(request, 'Você não tem permissão para editar esta venda.')
            return redirect('vendedor:vendas_list')
    
    if request.method == 'POST':
        form = VendasForm(request.POST, instance=venda)
        if form.is_valid():
            try:
                venda = form.save()
                messages.success(request, f'Venda para {venda.cliente.nome} atualizada com sucesso!')
                return redirect('vendedor:vendas_list')
            except Exception as e:
                logger.error(f"Erro ao atualizar venda: {str(e)}")
                messages.error(request, f'Erro ao atualizar venda: {str(e)}')
        else:
            messages.error(request, 'Corrija os erros abaixo.')
    else:
        form = VendasForm(instance=venda)
    
    context = {
        'form': form, 
        'title': f'Editar Venda #{venda.id}',
        'venda': venda,
        'is_edit': True,
        'is_vendedor_restrito': request.user.nivel == 'vendedor',
    }
    return render(request, 'vendedor/vendas_form.html', context)

@login_required
def vendas_detail(request, pk):
    """Detalhes da venda - COM CONTROLE DE ACESSO"""
    venda = get_object_or_404(Vendas.objects.select_related(
        'cliente', 'produto', 'produto__grupo', 'produto__fabricante', 'loja'
    ), pk=pk)
    
    # *** CONTROLE DE ACESSO: Verificar se vendedor pode ver esta venda ***
    if request.user.nivel == 'vendedor':
        if not request.user.pode_visualizar_vendedor(venda.cliente.codigo_vendedor):
            messages.error(request, 'Você não tem permissão para visualizar esta venda.')
            return redirect('vendedor:vendas_list')
    
    # Buscar outras vendas do mesmo cliente (com controle de acesso)
    vendas_relacionadas_query = Vendas.objects.filter(
        cliente=venda.cliente
    ).exclude(pk=venda.pk).order_by('-data_venda')
    
    # *** APLICAR CONTROLE DE ACESSO NAS VENDAS RELACIONADAS ***
    if request.user.nivel == 'vendedor':
        codigos_permitidos = request.user.get_codigos_vendedores_permitidos()
        if codigos_permitidos:
            vendas_relacionadas_query = vendas_relacionadas_query.filter(
                cliente__codigo_vendedor__in=codigos_permitidos
            )
        else:
            vendas_relacionadas_query = Vendas.objects.none()
    
    vendas_relacionadas = vendas_relacionadas_query[:5]
    
    context = {
        'venda': venda,
        'vendas_relacionadas': vendas_relacionadas,
        'is_vendedor_restrito': request.user.nivel == 'vendedor',
        'pode_editar': True if request.user.nivel in ['admin', 'gestor'] else request.user.pode_visualizar_vendedor(venda.cliente.codigo_vendedor),
    }
    
    return render(request, 'vendedor/vendas_detail.html', context)

@login_required
def vendas_delete(request, pk):
    """Deletar venda - COM CONTROLE DE ACESSO"""
    venda = get_object_or_404(Vendas, pk=pk)
    
    # *** CONTROLE DE ACESSO: Verificar se vendedor pode deletar esta venda ***
    if request.user.nivel == 'vendedor':
        if not request.user.pode_visualizar_vendedor(venda.cliente.codigo_vendedor):
            messages.error(request, 'Você não tem permissão para excluir esta venda.')
            return redirect('vendedor:vendas_list')
        
        # Vendedores podem ter restrição adicional para deletar
        messages.warning(request, 'Vendedores não podem excluir vendas. Entre em contato com o gestor.')
        return redirect('vendedor:vendas_detail', pk=pk)
    
    if request.method == 'POST':
        cliente_nome = venda.cliente.nome
        venda_id = venda.id
        venda.delete()
        messages.success(request, f'Venda #{venda_id} de {cliente_nome} excluída com sucesso!')
        return redirect('vendedor:vendas_list')
    
    context = {
        'venda': venda,
        'is_vendedor_restrito': request.user.nivel == 'vendedor',
    }
    return render(request, 'vendedor/vendas_confirm_delete.html', context)

@login_required
def vendas_update(request, pk):
    """View para editar venda (alias para vendas_edit)"""
    return vendas_edit(request, pk)