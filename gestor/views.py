# gestor/views.py - VERSÃO COMPLETA
import logging
from datetime import datetime, timedelta
import json
import requests
import ast
import pandas as pd
from decimal import Decimal
import re


from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Sum, Prefetch
from django.utils import timezone
from django.db import transaction

from core.models import (Cliente, ClienteContato, ClienteCnaeSecundario, 
                        Loja, Vendedor, GrupoProduto, Fabricante, Produto, Vendas)
from core.forms import (ClienteForm, ClienteContatoForm, ClienteCnaeSecundarioFormSet,
                       LojaForm, VendedorForm, GrupoProdutoForm, FabricanteForm, 
                       ProdutoForm, VendasForm, ImportarVendasForm)

logger = logging.getLogger(__name__)

# ===== FUNÇÕES AUXILIARES PARA CLIENTE =====

def parse_cnaes_secundarios(cnaes_string):
    """
    Converte string JSON dos CNAEs secundários em lista de dicionários
    """
    if not cnaes_string or cnaes_string in ['', 'NULL', 'null', '[]']:
        return []
    
    try:
        # Método 1: Tentar JSON padrão
        if cnaes_string.startswith('[') and cnaes_string.endswith(']'):
            try:
                # Corrigir aspas simples para aspas duplas
                cnaes_json = cnaes_string.replace("'", '"')
                cnaes_list = json.loads(cnaes_json)
            except json.JSONDecodeError:
                # Método 2: Usar ast.literal_eval (mais seguro para aspas simples)
                cnaes_list = ast.literal_eval(cnaes_string)
        else:
            return []
        
        # Filtrar CNAEs válidos e normalizar
        cnaes_validos = []
        for i, cnae in enumerate(cnaes_list):
            if isinstance(cnae, dict) and cnae.get('codigo') and cnae.get('codigo') != 0:
                cnaes_validos.append({
                    'codigo': str(cnae['codigo']).strip(),
                    'descricao': str(cnae.get('descricao', '')).strip(),
                    'ordem': i + 1
                })
        
        return cnaes_validos
        
    except Exception as e:
        logger.error(f"Erro ao parsear CNAEs secundários: {cnaes_string[:100]}... - {str(e)}")
        return []

def salvar_cnaes_secundarios(cliente, cnaes_secundarios_string):
    """
    Salva os CNAEs secundários de um cliente
    """
    # Limpar CNAEs secundários existentes
    ClienteCnaeSecundario.objects.filter(cliente=cliente).delete()
    
    # Parsear novos CNAEs
    cnaes_list = parse_cnaes_secundarios(cnaes_secundarios_string)
    
    # Salvar cada CNAE secundário
    cnaes_criados = []
    for cnae_data in cnaes_list:
        cnae_secundario = ClienteCnaeSecundario.objects.create(
            cliente=cliente,
            codigo_cnae=cnae_data['codigo'],
            descricao_cnae=cnae_data['descricao'],
            ordem=cnae_data['ordem']
        )
        cnaes_criados.append(cnae_secundario)
    
    return cnaes_criados

def processar_cnaes_receita(cliente, dados_receita):
    """
    Processa CNAEs vindos da consulta da Receita Federal
    """
    try:
        with transaction.atomic():
            # Atualizar CNAE principal
            cliente.cnae_principal = dados_receita.get('cnaeFiscal')
            cliente.cnae_descricao = dados_receita.get('cnaeFiscalDescricao')
            cliente.save()
            
            # Limpar CNAEs secundários existentes
            cliente.cnaes_secundarios.all().delete()
            
            # Adicionar novos CNAEs secundários
            cnaes_secundarios = dados_receita.get('cnaesSecundarios', [])
            for i, cnae_data in enumerate(cnaes_secundarios, 1):
                ClienteCnaeSecundario.objects.create(
                    cliente=cliente,
                    codigo_cnae=cnae_data['codigo'],
                    descricao_cnae=cnae_data['descricao'],
                    ordem=i
                )
                
        return True, f"CNAEs atualizados: 1 principal + {len(cnaes_secundarios)} secundários"
        
    except Exception as e:
        return False, f"Erro ao processar CNAEs: {str(e)}"

# ===== PÁGINAS PRINCIPAIS =====

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

# ===== CRUD CLIENTE =====

@login_required
def cliente_list(request):
    # Filtros múltiplos
    
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

# ===== GERENCIAMENTO DE CONTATOS (CLIENTE) =====

@login_required
def cliente_contato_create(request, cliente_id):
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

# ===== CRUD LOJA =====

@login_required
def loja_list(request):
    search = request.GET.get('search', '')
    lojas = Loja.objects.all()
    
    if search:
        lojas = lojas.filter(
            Q(codigo__icontains=search) |
            Q(nome__icontains=search)
        )
    
    context = {'lojas': lojas, 'search': search}
    return render(request, 'gestor/loja_list.html', context)

@login_required
def loja_create(request):
    if request.method == 'POST':
        form = LojaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Loja criada com sucesso!')
            return redirect('gestor:loja_list')
    else:
        form = LojaForm()
    
    context = {'form': form, 'title': 'Nova Loja'}
    return render(request, 'gestor/loja_form.html', context)

@login_required
def loja_edit(request, pk):
    loja = get_object_or_404(Loja, codigo=pk)
    
    if request.method == 'POST':
        form = LojaForm(request.POST, instance=loja)
        if form.is_valid():
            form.save()
            messages.success(request, 'Loja atualizada com sucesso!')
            return redirect('gestor:loja_list')
    else:
        form = LojaForm(instance=loja)
    
    context = {'form': form, 'title': 'Editar Loja', 'loja': loja}
    return render(request, 'gestor/loja_form.html', context)

@login_required
def loja_delete(request, pk):
    loja = get_object_or_404(Loja, codigo=pk)
    
    if request.method == 'POST':
        loja.delete()
        messages.success(request, 'Loja excluída com sucesso!')
        return redirect('gestor:loja_list')
    
    context = {'loja': loja}
    return render(request, 'gestor/loja_confirm_delete.html', context)

# ===== CRUD VENDEDOR =====

# Adicione estas views corrigidas ao seu gestor/views.py

@login_required
def vendedor_list(request):
    search = request.GET.get('search', '')
    vendedores = Vendedor.objects.select_related('loja').all()
    
    if search:
        vendedores = vendedores.filter(
            Q(codigo__icontains=search) |
            Q(nome__icontains=search) |
            Q(loja__nome__icontains=search)
        )
    
    # Ordenar por código
    vendedores = vendedores.order_by('codigo')
    
    context = {
        'vendedores': vendedores, 
        'search': search
    }
    return render(request, 'gestor/vendedor_list.html', context)

@login_required
def vendedor_create(request):
    if request.method == 'POST':
        form = VendedorForm(request.POST)
        if form.is_valid():
            try:
                vendedor = form.save()
                messages.success(request, f'Vendedor "{vendedor.nome}" criado com sucesso!')
                return redirect('gestor:vendedor_list')
            except Exception as e:
                messages.error(request, f'Erro ao criar vendedor: {str(e)}')
        else:
            messages.error(request, 'Corrija os erros abaixo.')
    else:
        form = VendedorForm()
    
    context = {
        'form': form, 
        'title': 'Novo Vendedor',
        'is_create': True
    }
    return render(request, 'gestor/vendedor_form.html', context)

@login_required
def vendedor_edit(request, pk):
    try:
        vendedor = get_object_or_404(Vendedor, codigo=pk)
    except Exception as e:
        messages.error(request, f'Vendedor com código "{pk}" não encontrado.')
        return redirect('gestor:vendedor_list')
    
    if request.method == 'POST':
        form = VendedorForm(request.POST, instance=vendedor)
        if form.is_valid():
            try:
                vendedor = form.save()
                messages.success(request, f'Vendedor "{vendedor.nome}" atualizado com sucesso!')
                return redirect('gestor:vendedor_list')
            except Exception as e:
                messages.error(request, f'Erro ao atualizar vendedor: {str(e)}')
        else:
            messages.error(request, 'Corrija os erros abaixo.')
    else:
        form = VendedorForm(instance=vendedor)
    
    context = {
        'form': form, 
        'title': f'Editar Vendedor - {vendedor.nome}',
        'vendedor': vendedor,
        'is_edit': True
    }
    return render(request, 'gestor/vendedor_form.html', context)

@login_required
def vendedor_delete(request, pk):
    try:
        vendedor = get_object_or_404(Vendedor, codigo=pk)
    except Exception as e:
        messages.error(request, f'Vendedor com código "{pk}" não encontrado.')
        return redirect('gestor:vendedor_list')
    
    if request.method == 'POST':
        try:
            vendedor_nome = vendedor.nome
            vendedor.delete()
            messages.success(request, f'Vendedor "{vendedor_nome}" excluído com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao excluir vendedor: {str(e)}')
        return redirect('gestor:vendedor_list')
    
    # Verificar se o vendedor tem vendas associadas
    vendas_count = vendedor.vendas_set.count() if hasattr(vendedor, 'vendas_set') else 0
    
    context = {
        'vendedor': vendedor,
        'vendas_count': vendas_count
    }
    return render(request, 'gestor/vendedor_confirm_delete.html', context)


# ===== CRUD FABRICANTE =====

@login_required
def fabricante_list(request):
    search = request.GET.get('search', '')
    fabricantes = Fabricante.objects.all()
    
    if search:
        fabricantes = fabricantes.filter(
            Q(codigo__icontains=search) |
            Q(descricao__icontains=search)
        )
    
    context = {'fabricantes': fabricantes, 'search': search}
    return render(request, 'gestor/fabricante_list.html', context)

@login_required
def fabricante_create(request):
    if request.method == 'POST':
        form = FabricanteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fabricante criado com sucesso!')
            return redirect('gestor:fabricante_list')
    else:
        form = FabricanteForm()
    
    context = {'form': form, 'title': 'Novo Fabricante'}
    return render(request, 'gestor/fabricante_form.html', context)

@login_required
def fabricante_edit(request, pk):
    fabricante = get_object_or_404(Fabricante, codigo=pk)
    
    if request.method == 'POST':
        form = FabricanteForm(request.POST, instance=fabricante)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fabricante atualizado com sucesso!')
            return redirect('gestor:fabricante_list')
    else:
        form = FabricanteForm(instance=fabricante)
    
    context = {'form': form, 'title': 'Editar Fabricante', 'fabricante': fabricante}
    return render(request, 'gestor/fabricante_form.html', context)

@login_required
def fabricante_delete(request, pk):
    fabricante = get_object_or_404(Fabricante, codigo=pk)
    
    if request.method == 'POST':
        fabricante.delete()
        messages.success(request, 'Fabricante excluído com sucesso!')
        return redirect('gestor:fabricante_list')
    
    context = {'fabricante': fabricante}
    return render(request, 'gestor/fabricante_confirm_delete.html', context)

# ===== CRUD GRUPO PRODUTO =====

@login_required
def grupo_list(request):
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
    grupo = get_object_or_404(GrupoProduto, codigo=pk)
    
    if request.method == 'POST':
        grupo.delete()
        messages.success(request, 'Grupo de produto excluído com sucesso!')
        return redirect('gestor:grupo_list')
    
    context = {'grupo': grupo}
    return render(request, 'gestor/grupo_confirm_delete.html', context)

# ===== CRUD PRODUTO =====

@login_required
def produto_list(request):
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
    produto = get_object_or_404(Produto, codigo=pk)
    
    if request.method == 'POST':
        produto.delete()
        messages.success(request, 'Produto excluído com sucesso!')
        return redirect('gestor:produto_list')
    
    context = {'produto': produto}
    return render(request, 'gestor/produto_confirm_delete.html', context)

# ===== CRUD VENDAS =====

@login_required
def vendas_list(request):
    search = request.GET.get('search', '')
    vendas = Vendas.objects.select_related(
        'cliente', 'produto', 'loja', 'vendedor', 'grupo_produto', 'fabricante'
    ).all()
    
    if search:
        vendas = vendas.filter(
            Q(cliente__nome__icontains=search) |
            Q(produto__descricao__icontains=search) |
            Q(numero_nf__icontains=search)
        )
    
    paginator = Paginator(vendas, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'page_obj': page_obj, 'search': search}
    return render(request, 'gestor/vendas_list.html', context)

@login_required
def vendas_create(request):
    if request.method == 'POST':
        form = VendasForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Venda criada com sucesso!')
            return redirect('gestor:vendas_list')
    else:
        form = VendasForm()
    
    context = {'form': form, 'title': 'Nova Venda'}
    return render(request, 'gestor/vendas_form.html', context)

@login_required
def vendas_edit(request, pk):
    venda = get_object_or_404(Vendas, pk=pk)
    
    if request.method == 'POST':
        form = VendasForm(request.POST, instance=venda)
        if form.is_valid():
            form.save()
            messages.success(request, 'Venda atualizada com sucesso!')
            return redirect('gestor:vendas_list')
    else:
        form = VendasForm(instance=venda)
    
    context = {'form': form, 'title': 'Editar Venda', 'venda': venda}
    return render(request, 'gestor/vendas_form.html', context)

@login_required
def vendas_delete(request, pk):
    venda = get_object_or_404(Vendas, pk=pk)
    
    if request.method == 'POST':
        venda.delete()
        messages.success(request, 'Venda excluída com sucesso!')
        return redirect('gestor:vendas_list')
    
    context = {'venda': venda}
    return render(request, 'gestor/vendas_confirm_delete.html', context)

# ===== IMPORTAÇÃO DE VENDAS =====


# VERSÃO CORRIGIDA da função importar_vendas


@login_required
def importar_vendas(request):
    if request.method == 'POST':
        form = ImportarVendasForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                arquivo = request.FILES['arquivo_csv']  # Pode ser CSV ou Excel
                limpar_registros = form.cleaned_data['limpar_registros_anteriores']
                criar_dependencias = form.cleaned_data['criar_dependencias']
                status_cliente_novo = form.cleaned_data['status_cliente_novo']
                
                # Detectar tipo de arquivo e ler
                nome_arquivo = arquivo.name.lower()
                
                try:
                    if nome_arquivo.endswith('.xlsx') or nome_arquivo.endswith('.xls'):
                        # Ler arquivo Excel - especificar engine
                        df = pd.read_excel(arquivo, sheet_name=0, engine='openpyxl' if nome_arquivo.endswith('.xlsx') else 'xlrd')
                    elif nome_arquivo.endswith('.csv'):
                        # Ler arquivo CSV com diferentes encodings
                        try:
                            df = pd.read_csv(arquivo, encoding='utf-8', sep=',')
                        except UnicodeDecodeError:
                            # Tentar com encoding latin-1
                            arquivo.seek(0)  # Voltar ao início do arquivo
                            df = pd.read_csv(arquivo, encoding='latin-1', sep=',')
                    else:
                        raise ValueError("Formato de arquivo não suportado. Use CSV (.csv) ou Excel (.xlsx, .xls).")
                except ImportError as e:
                    if 'openpyxl' in str(e):
                        raise ValueError("Para ler arquivos Excel (.xlsx), instale: pip install openpyxl")
                    elif 'xlrd' in str(e):
                        raise ValueError("Para ler arquivos Excel (.xls), instale: pip install xlrd")
                    else:
                        raise ValueError(f"Erro ao ler arquivo: {str(e)}")
                
                # Normalizar nomes das colunas (remover espaços e converter para maiúsculo)
                df.columns = df.columns.str.strip().str.upper()
                
                # Verificar se as colunas necessárias existem
                colunas_necessarias = [
                    'CLIENTE', 'ANOMES', 'VEND', 'NUMLOJ', 'PRODUTO', 'CLASSE', 
                    'QTD', 'TOTAL', 'NF', 'CNPJ', 'CODPRO', 'ANO', 'MES', 'UF', 'CODVEN'
                ]
                
                # Verificar colunas disponíveis
                colunas_disponiveis = list(df.columns)
                colunas_faltando = [col for col in colunas_necessarias if col not in colunas_disponiveis]
                
                if colunas_faltando:
                    raise ValueError(
                        f"Colunas obrigatórias não encontradas: {', '.join(colunas_faltando)}.\n"
                        f"Colunas disponíveis no arquivo: {', '.join(colunas_disponiveis)}"
                    )
                
                # Remover linhas completamente vazias
                df = df.dropna(how='all')
                
                if df.empty:
                    raise ValueError("O arquivo não contém dados válidos.")
                
                # Contadores
                vendas_criadas = 0
                clientes_criados = 0
                produtos_criados = 0
                grupos_criados = 0
                fabricantes_criados = 0
                lojas_criadas = 0
                vendedores_criados = 0
                erros = []
                duplicatas_ignoradas = 0
                
                # Limpar registros anteriores se solicitado
                if limpar_registros:
                    count_deletados = Vendas.objects.all().count()
                    Vendas.objects.all().delete()
                    messages.info(request, f'{count_deletados} registros de vendas anteriores foram removidos.')
                
                # Processar cada linha
                total_linhas = len(df)
                for index, row in df.iterrows():
                    try:
                        with transaction.atomic():
                            # Verificar se a linha tem dados mínimos necessários
                            if pd.isna(row['CLIENTE']) or pd.isna(row['PRODUTO']) or pd.isna(row['CODPRO']):
                                erros.append(f"Linha {index + 2}: Dados obrigatórios ausentes (CLIENTE, PRODUTO ou CODPRO)")
                                continue
                            
                            # Extrair e limpar dados
                            nome_cliente = str(row['CLIENTE']).strip()
                            anomes = str(row['ANOMES']).strip()
                            nome_vendedor = str(row['VEND']).strip() if pd.notna(row['VEND']) else 'VENDEDOR PADRÃO'
                            
                            # Tratar códigos numéricos que podem vir como float
                            try:
                                codigo_loja = str(int(float(row['NUMLOJ']))).zfill(3) if pd.notna(row['NUMLOJ']) else '001'
                            except (ValueError, OverflowError):
                                codigo_loja = '001'
                                
                            desc_produto = str(row['PRODUTO']).strip()
                            desc_classe = str(row['CLASSE']).strip() if pd.notna(row['CLASSE']) else 'CLASSE PADRÃO'
                            
                            # Valores numéricos
                            try:
                                quantidade = Decimal(str(row['QTD']).replace(',', '.')) if pd.notna(row['QTD']) else Decimal('1')
                                valor_total = Decimal(str(row['TOTAL']).replace(',', '.')) if pd.notna(row['TOTAL']) else Decimal('0')
                            except (ValueError, TypeError):
                                erros.append(f"Linha {index + 2}: Valores numéricos inválidos (QTD ou TOTAL)")
                                continue
                            
                            # Outros campos
                            numero_nf = str(int(float(row['NF']))) if pd.notna(row['NF']) and row['NF'] != '' else ''
                            cnpj = str(row['CNPJ']).strip() if pd.notna(row['CNPJ']) else ''
                            
                            try:
                                codigo_produto = str(int(float(row['CODPRO']))).zfill(6)  # Garantir 6 dígitos
                            except (ValueError, OverflowError):
                                erros.append(f"Linha {index + 2}: Código de produto inválido: {row['CODPRO']}")
                                continue
                                
                            ano = str(row['ANO']).strip() if pd.notna(row['ANO']) else '24'
                            mes = str(int(float(row['MES']))).zfill(2) if pd.notna(row['MES']) else '01'
                            uf = str(row['UF']).strip() if pd.notna(row['UF']) else 'SP'
                            
                            try:
                                codigo_vendedor = str(int(float(row['CODVEN']))).zfill(3) if pd.notna(row['CODVEN']) else '001'
                            except (ValueError, OverflowError):
                                codigo_vendedor = '001'
                            
                            # Gerar códigos baseados nos dados
                            # Código do cliente: usar CNPJ se disponível, senão gerar baseado no nome
                            if cnpj and len(cnpj.replace('.', '').replace('/', '').replace('-', '')) >= 10:
                                # Limpar CNPJ e usar primeiros 10 dígitos
                                cnpj_limpo = ''.join(filter(str.isdigit, cnpj))
                                codigo_cliente = cnpj_limpo[:10] if len(cnpj_limpo) >= 10 else cnpj_limpo.ljust(10, '0')
                            else:
                                # Gerar código baseado no nome (primeiras letras)
                                palavras = re.findall(r'\b\w+', nome_cliente.upper())
                                codigo_cliente = ''.join([p[:2] for p in palavras[:3]])[:6]
                                if len(codigo_cliente) < 6:
                                    codigo_cliente = codigo_cliente.ljust(6, '0')
                                # Adicionar sufixo numérico para garantir unicidade
                                codigo_cliente = f"CLI{codigo_cliente}"[:10]
                            
                            # Código da classe/grupo: baseado na descrição (garantir 4 dígitos numéricos)
                            palavras_classe = re.findall(r'\b\w+', desc_classe.upper())
                            if palavras_classe:
                                codigo_classe = ''.join([p[:2] for p in palavras_classe[:2]])[:4]
                                # Converter para numérico se possível, senão usar hash
                                codigo_numerico = ''.join(filter(str.isdigit, codigo_classe))
                                if len(codigo_numerico) >= 4:
                                    codigo_classe = codigo_numerico[:4]
                                else:
                                    # Usar hash da descrição para gerar código numérico
                                    hash_valor = abs(hash(desc_classe)) % 10000
                                    codigo_classe = str(hash_valor).zfill(4)
                            else:
                                codigo_classe = '0001'
                            
                            # Código do fabricante: extrair da descrição do produto
                            desc_upper = desc_produto.upper()
                            if 'FUJI' in desc_upper:
                                codigo_fabricante = 'FUJI'
                            elif 'KODAK' in desc_upper:
                                codigo_fabricante = 'KODAK'
                            elif 'CANON' in desc_upper:
                                codigo_fabricante = 'CANON'
                            elif 'NIKON' in desc_upper:
                                codigo_fabricante = 'NIKON'
                            elif 'SONY' in desc_upper:
                                codigo_fabricante = 'SONY'
                            elif 'SAMSUNG' in desc_upper:
                                codigo_fabricante = 'SAMSUNG'
                            else:
                                # Usar primeira palavra ou código genérico
                                primeira_palavra = desc_produto.split()[0][:6] if desc_produto else 'GENERICO'
                                codigo_fabricante = primeira_palavra.upper()
                            
                            # Converter ANOMES para data (formato: AAMM -> 20AA-MM-01)
                            try:
                                if len(anomes) == 4 and anomes.isdigit():
                                    ano_completo = '20' + anomes[:2]
                                    mes_num = anomes[2:]
                                    data_venda = datetime.strptime(f"{ano_completo}-{mes_num}-01", '%Y-%m-%d').date()
                                else:
                                    # Tentar usar ano e mês separados
                                    ano_int = int(ano) if ano.isdigit() else 24
                                    mes_int = int(mes) if mes.isdigit() else 1
                                    ano_completo = 2000 + ano_int if ano_int < 100 else ano_int
                                    data_venda = datetime(ano_completo, mes_int, 1).date()
                            except (ValueError, TypeError):
                                erros.append(f"Linha {index + 2}: Data inválida - ANOMES: {anomes}, ANO: {ano}, MES: {mes}")
                                continue
                            
                            if criar_dependencias:
                                # Criar/buscar Fabricante
                                fabricante, criado = Fabricante.objects.get_or_create(
                                    codigo=codigo_fabricante,
                                    defaults={'descricao': codigo_fabricante}
                                )
                                if criado:
                                    fabricantes_criados += 1
                                
                                # Criar/buscar Grupo (Classe)
                                grupo, criado = GrupoProduto.objects.get_or_create(
                                    codigo=codigo_classe,
                                    defaults={'descricao': desc_classe[:100]}  # Limitar tamanho
                                )
                                if criado:
                                    grupos_criados += 1
                                
                                # Criar/buscar Loja
                                loja, criado = Loja.objects.get_or_create(
                                    codigo=codigo_loja,
                                    defaults={'nome': f'Loja {codigo_loja}'}
                                )
                                if criado:
                                    lojas_criadas += 1
                                
                                # Criar/buscar Vendedor
                                vendedor, criado = Vendedor.objects.get_or_create(
                                    codigo=codigo_vendedor,
                                    defaults={
                                        'nome': nome_vendedor[:100],  # Limitar tamanho
                                        'loja': loja
                                    }
                                )
                                if criado:
                                    vendedores_criados += 1
                                
                                # Criar/buscar Cliente
                                cliente, criado = Cliente.objects.get_or_create(
                                    codigo=codigo_cliente,
                                    defaults={
                                        'nome': nome_cliente[:100],  # Limitar tamanho
                                        'status': status_cliente_novo,
                                        'cpf_cnpj': cnpj,
                                        'tipo_documento': 'cnpj' if len(cnpj.replace('.', '').replace('/', '').replace('-', '')) == 14 else 'cpf',
                                        'codigo_loja': codigo_loja,
                                        'codigo_vendedor': codigo_vendedor,
                                        'nome_vendedor': nome_vendedor[:100],
                                        'uf': uf
                                    }
                                )
                                if criado:
                                    clientes_criados += 1
                                
                                # Criar/buscar Produto
                                produto, criado = Produto.objects.get_or_create(
                                    codigo=codigo_produto,
                                    defaults={
                                        'descricao': desc_produto[:200],  # Limitar tamanho
                                        'grupo': grupo,
                                        'fabricante': fabricante
                                    }
                                )
                                if criado:
                                    produtos_criados += 1
                            else:
                                # Buscar entidades existentes
                                try:
                                    fabricante = Fabricante.objects.get(codigo=codigo_fabricante)
                                    grupo = GrupoProduto.objects.get(codigo=codigo_classe)
                                    loja = Loja.objects.get(codigo=codigo_loja)
                                    vendedor = Vendedor.objects.get(codigo=codigo_vendedor)
                                    cliente = Cliente.objects.get(codigo=codigo_cliente)
                                    produto = Produto.objects.get(codigo=codigo_produto)
                                except Exception as e:
                                    erros.append(f"Linha {index + 2}: Dependência não encontrada: {str(e)}")
                                    continue
                            
                            # Verificar se a venda já existe (evitar duplicatas)
                            venda_existente = Vendas.objects.filter(
                                data_venda=data_venda,
                                cliente=cliente,
                                produto=produto,
                                numero_nf=numero_nf,
                                valor_total=valor_total
                            ).exists()
                            
                            if not venda_existente:
                                # Criar venda
                                venda = Vendas.objects.create(
                                    data_venda=data_venda,
                                    cliente=cliente,
                                    produto=produto,
                                    grupo_produto=grupo,
                                    fabricante=fabricante,
                                    loja=loja,
                                    vendedor=vendedor,
                                    quantidade=quantidade,
                                    valor_total=valor_total,
                                    numero_nf=numero_nf,
                                    estado=uf
                                )
                                vendas_criadas += 1
                            else:
                                duplicatas_ignoradas += 1
                            
                    except Exception as e:
                        erros.append(f"Linha {index + 2}: Erro: {str(e)}")
                        continue
                    
                    # Log de progresso a cada 1000 registros
                    if (index + 1) % 1000 == 0:
                        logger.info(f"Processadas {index + 1}/{total_linhas} linhas")
                
                # Mensagem de resultado
                mensagem_sucesso = f"Importação concluída! {vendas_criadas} vendas importadas de {total_linhas} registros."
                
                if duplicatas_ignoradas > 0:
                    mensagem_sucesso += f" {duplicatas_ignoradas} duplicatas ignoradas."
                
                if criar_dependencias:
                    detalhes = []
                    if clientes_criados > 0:
                        detalhes.append(f"{clientes_criados} clientes")
                    if produtos_criados > 0:
                        detalhes.append(f"{produtos_criados} produtos")
                    if grupos_criados > 0:
                        detalhes.append(f"{grupos_criados} grupos")
                    if fabricantes_criados > 0:
                        detalhes.append(f"{fabricantes_criados} fabricantes")
                    if lojas_criadas > 0:
                        detalhes.append(f"{lojas_criadas} lojas")
                    if vendedores_criados > 0:
                        detalhes.append(f"{vendedores_criados} vendedores")
                    
                    if detalhes:
                        mensagem_sucesso += f" Criados: {', '.join(detalhes)}."
                
                messages.success(request, mensagem_sucesso)
                
                # Mostrar erros se houver
                if erros:
                    messages.warning(request, f"{len(erros)} linhas com erro foram ignoradas.")
                    for erro in erros[:5]:  # Mostrar os primeiros 5 erros
                        messages.error(request, erro)
                    if len(erros) > 5:
                        messages.warning(request, f"... e mais {len(erros) - 5} erros. Verifique o log para detalhes.")
                
                return redirect('gestor:vendas_list')
                
            except Exception as e:
                logger.error(f"Erro na importação: {str(e)}")
                messages.error(request, f'Erro ao processar arquivo: {str(e)}')
    else:
        form = ImportarVendasForm()
    
    context = {'form': form, 'title': 'Importar Vendas do BI'}
    return render(request, 'gestor/importar_vendas.html', context)

# ===== API E CONSULTAS EXTERNAS =====

@login_required
def api_cliente_por_codigo(request, codigo):
    """API para buscar cliente por código"""
    cliente = Cliente.objects.filter(codigo=codigo).first()
    
    if cliente:
        return JsonResponse({
            'success': True,
            'id': cliente.id,
            'nome': cliente.nome,
            'cpf_cnpj': cliente.cpf_cnpj
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Cliente não encontrado'
        })
    
@login_required
def api_consultar_receita(request, cpf_cnpj):
    """API para consultar dados na Receita Federal com CNAEs múltiplos"""
    # Remover caracteres não numéricos
    cpf_cnpj = ''.join(filter(str.isdigit, cpf_cnpj))
    
    try:
        # Simulação de resposta com CNAEs secundários
        if len(cpf_cnpj) == 11:  # CPF
            dados = {
                'tipo': 'PF',
                'razaoSocial': 'NOME DA PESSOA FÍSICA',
                'situacaoCadastral': 'ATIVA',
                'dataSituacaoCadastral': '2020-01-01',
                'motivoSituacaoCadastral': 'SEM MOTIVO',
            }
        else:  # CNPJ
            dados = {
                'tipo': 'PJ',
                'razaoSocial': 'EMPRESA DEMONSTRACAO LTDA',
                'nomeFantasia': 'DEMO EMPRESA',
                'situacaoCadastral': 'ATIVA',
                'dataSituacaoCadastral': '2020-01-01',
                'motivoSituacaoCadastral': 'SEM MOTIVO',
                'cnaeFiscal': '4751201',
                'cnaeFiscalDescricao': 'COMÉRCIO VAREJISTA ESPECIALIZADO DE EQUIPAMENTOS DE INFORMÁTICA',
                'naturezaJuridica': '206-2 - SOCIEDADE EMPRESÁRIA LIMITADA',
                'porteEmpresa': 'ME',
                'dataAbertura': '2010-01-01',
                'endereco': {
                    'tipoLogradouro': 'RUA',
                    'logradouro': 'DAS FLORES',
                    'numero': '123',
                    'complemento': 'SALA 1',
                    'bairro': 'CENTRO',
                    'municipio': 'SÃO PAULO',
                    'uf': 'SP',
                    'cep': '01310-000'
                },
                'optanteSimples': True,
                'optanteMei': False,
                # CNAEs secundários para testar
                'cnaesSecundarios': [
                    {'codigo': '4647801', 'descricao': 'Comércio atacadista de artigos de escritório e de papelaria'},
                    {'codigo': '4651602', 'descricao': 'Comércio atacadista de suprimentos para informática'},
                    {'codigo': '8219901', 'descricao': 'Fotocópias'},
                    {'codigo': '6201501', 'descricao': 'Desenvolvimento de programas de computador sob encomenda'}
                ]
            }
        
        return JsonResponse({
            'success': True,
            'dados': dados
        })
        
    except Exception as e:
        logger.error(f"Erro ao consultar dados na Receita: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Erro ao consultar dados: {str(e)}'
        })

# ===== FUNÇÃO PARA CONSULTAR BI =====

@login_required
def consultar_bi(request, codigo_cliente):
    """View para consultar BI do cliente"""
    cliente = get_object_or_404(Cliente, codigo=codigo_cliente)
    
    # Parâmetros de filtro
    filtro_periodo = request.GET.get('periodo', '90')  # Padrão: últimos 90 dias
    data_inicio = None
    data_fim = timezone.now().date()
    
    try:
        dias = int(filtro_periodo)
        data_inicio = data_fim - timedelta(days=dias)
    except ValueError:
        # Se período não for um número válido, usar 90 dias
        data_inicio = data_fim - timedelta(days=90)
    
    # Obter códigos de todos os clientes (principal + associados)
    codigos_clientes = [cliente.codigo]
    
    # Se for cliente principal, adicionar sub-clientes
    if not cliente.codigo_master:
        clientes_associados = Cliente.objects.filter(codigo_master=cliente.codigo)
        codigos_clientes.extend([c.codigo for c in clientes_associados])
    
    # Buscar dados de vendas
    try:
        vendas = Vendas.objects.filter(
            cliente__codigo__in=codigos_clientes,
            data_venda__gte=data_inicio,
            data_venda__lte=data_fim
        ).order_by('-data_venda')
        
        # Calcular totais
        total_vendas = vendas.aggregate(
            total_valor=Sum('valor_total'),
            total_quantidade=Sum('quantidade')
        )
        
        # Verificar formato de saída
        formato = request.GET.get('format', 'html')
        if formato == 'json':
            # Retornar dados em formato JSON
            dados = {
                'cliente': {
                    'codigo': cliente.codigo,
                    'nome': cliente.nome,
                },
                'periodo': {
                    'inicio': data_inicio.strftime('%d/%m/%Y'),
                    'fim': data_fim.strftime('%d/%m/%Y'),
                },
                'totais': {
                    'valor': float(total_vendas['total_valor'] or 0),
                    'quantidade': float(total_vendas['total_quantidade'] or 0),
                },
                'vendas': [
                    {
                        'data': v.data_venda.strftime('%d/%m/%Y'),
                        'produto': {
                            'codigo': v.produto.codigo,
                            'descricao': v.produto.descricao,
                        },
                        'quantidade': float(v.quantidade),
                        'valor': float(v.valor_total),
                    } for v in vendas[:100]  # Limitar a 100 registros
                ]
            }
            return JsonResponse(dados)
        else:
            # Retornar template HTML
            return render(request, 'gestor/cliente_bi.html', {
                'cliente': cliente,
                'vendas': vendas,
                'data_inicio': data_inicio,
                'data_fim': data_fim,
                'total_valor': total_vendas['total_valor'] or 0,
                'total_quantidade': total_vendas['total_quantidade'] or 0,
                'filtro_periodo': filtro_periodo,
            })
    
    except Exception as e:
        logger.error(f"Erro ao consultar BI: {str(e)}")
        if request.GET.get('format') == 'json':
            return JsonResponse({
                'success': False,
                'message': f'Erro ao consultar dados: {str(e)}'
            })
        else:
            messages.error(request, f'Erro ao consultar dados de BI: {str(e)}')
            return redirect('gestor:cliente_detail', pk=cliente.id)