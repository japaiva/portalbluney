# gestor/views/cliente.py - VERSÃO ATUALIZADA

import logging
from datetime import datetime, timedelta
import json
import requests
import ast

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Sum, Prefetch
from django.utils import timezone
from django.db import transaction

from core.models import Cliente, ClienteContato, ClienteCnaeSecundario, RegistroBI
from core.forms import ClienteForm, ClienteContatoForm, ClienteCnaeSecundarioFormSet

logger = logging.getLogger(__name__)

# Função auxiliar para parsear CNAEs secundários
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

# Páginas principais
@login_required
def home(request):
    """
    Página inicial do Portal do Gestor
    """
    return render(request, 'gestor/home.html')

@login_required
def dashboard(request):
    """View para o dashboard do gestor"""
    return render(request, 'gestor/dashboard.html')

# CRUD Clientes - VERSÃO ATUALIZADA COM FILTROS MÚLTIPLOS
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
        clientes_list = clientes_list.filter(ativo=True)
    elif status == 'inativo':
        clientes_list = clientes_list.filter(ativo=False)
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
    paginator = Paginator(clientes_list, 15)  # Aumentado para 15 por página
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
        'cnaes_formset': cnaes_formset,  # ← Adicionado!
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
        'cnaes_formset': cnaes_formset,  # ← Adicionado!
        'cliente': cliente,
        'cliente_master_nome': cliente_master.nome if cliente_master else None
    }
    
    return render(request, 'gestor/cliente_form.html', context)
@login_required
def cliente_toggle_status(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    cliente.ativo = not cliente.ativo
    cliente.save()
    
    status = "ativado" if cliente.ativo else "desativado"
    messages.success(request, f'Cliente "{cliente.nome}" {status} com sucesso.')
    
    # Retornar para a página anterior
    return_url = request.META.get('HTTP_REFERER', 'gestor:cliente_list')
    return redirect(return_url)

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
        # Verificar se o modelo RegistroBI está disponível
        vendas_recentes = RegistroBI.objects.filter(
            cliente__codigo__in=codigos_clientes,
            data_venda__gte=data_inicio,
            ativo=True
        ).order_by('-data_venda')[:10]
        
        # Calcular total de vendas no período
        total_vendas_recentes = RegistroBI.objects.filter(
            cliente__codigo__in=codigos_clientes,
            data_venda__gte=data_inicio,
            ativo=True
        ).aggregate(total=Sum('valor_total'))['total'] or 0
    except:
        logger.warning("Modelo RegistroBI não disponível ou ocorreu um erro ao buscar dados de vendas")
    
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

# Gerenciamento de Contatos (mantido igual)
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

# API e Consultas Externas - VERSÃO ATUALIZADA
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
            'dados': dados  # ← Estrutura corrigida para o JavaScript
        })
        
    except Exception as e:
        logger.error(f"Erro ao consultar dados na Receita: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Erro ao consultar dados: {str(e)}'
        })

# Função para consultar BI (mantida igual)
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
        vendas = RegistroBI.objects.filter(
            cliente__codigo__in=codigos_clientes,
            data_venda__gte=data_inicio,
            data_venda__lte=data_fim,
            ativo=True
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