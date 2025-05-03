# gestor/views/cliente.py

import logging
from datetime import datetime, timedelta
import json
import requests

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Sum
from django.utils import timezone

from core.models import Cliente, ClienteContato, RegistroBI
from core.forms import ClienteForm, ClienteContatoForm

logger = logging.getLogger(__name__)

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

# CRUD Clientes
@login_required
def cliente_list(request):
    # Mostrar apenas clientes principais (sem código master)
    clientes_list = Cliente.objects.filter(
        Q(codigo_master__isnull=True) | Q(codigo_master='')
    ).order_by('nome')
    
    # Filtro por status
    status = request.GET.get('status')
    if status == 'ativo':
        clientes_list = clientes_list.filter(ativo=True)
    elif status == 'inativo':
        clientes_list = clientes_list.filter(ativo=False)
    
    # Busca por nome, código ou CPF/CNPJ
    query = request.GET.get('q')
    if query:
        clientes_list = clientes_list.filter(
            Q(nome__icontains=query) | 
            Q(codigo__icontains=query) |
            Q(cpf_cnpj__icontains=query)
        )
    
    # Paginação
    paginator = Paginator(clientes_list, 10)
    page = request.GET.get('page', 1)
    
    try:
        clientes = paginator.page(page)
    except PageNotAnInteger:
        clientes = paginator.page(1)
    except EmptyPage:
        clientes = paginator.page(paginator.num_pages)
    
    return render(request, 'gestor/cliente_list.html', {
        'clientes': clientes, 
        'status_filtro': status,
        'query': query
    })

@login_required
def cliente_create(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f'Cliente "{cliente.nome}" cadastrado com sucesso.')
            return redirect('gestor:cliente_detail', pk=cliente.id)
    else:
        # Verificar se é um sub-cliente sendo criado
        codigo_master = request.GET.get('codigo_master', '')
        initial_data = {}
        cliente_master = None
        
        if codigo_master:
            inicial_data = {'codigo_master': codigo_master}
            cliente_master = Cliente.objects.filter(codigo=codigo_master).first()
        
        form = ClienteForm(initial=inicial_data)
    
    context = {
        'form': form,
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
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f'Cliente "{cliente.nome}" atualizado com sucesso.')
            return redirect('gestor:cliente_detail', pk=cliente.id)
    else:
        form = ClienteForm(instance=cliente)
    
    context = {
        'form': form, 
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

# Gerenciamento de Contatos
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

# API e Consultas Externas
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
    """API para consultar dados na Receita Federal"""
    # Remover caracteres não numéricos
    cpf_cnpj = ''.join(filter(str.isdigit, cpf_cnpj))
    
    try:
        # Aqui você implementaria a chamada para o serviço de consulta da Receita
        # Este é um exemplo simulado
        
        # Em ambiente de produção, substituir por chamada real ao serviço
        # response = requests.get(f"https://api.consulta-receita.com/v1/{cpf_cnpj}", 
        #                         headers={"Authorization": "Bearer seu_token"})
        # dados = response.json()
        
        # Simulação de resposta para testes
        if len(cpf_cnpj) == 11:  # CPF
            dados = {
                'tipo': 'PF',
                'nome': 'NOME DA PESSOA FÍSICA',
                'situacaoCadastral': 'REGULAR',
            }
        else:  # CNPJ
            dados = {
                'tipo': 'PJ',
                'razaoSocial': 'EMPRESA DEMONSTRACAO LTDA',
                'nomeFantasia': 'DEMO EMPRESA',
                'situacaoCadastral': 'ATIVA',
                'cnae': '4751-2/01',
                'cnaeDescricao': 'COMÉRCIO VAREJISTA ESPECIALIZADO DE EQUIPAMENTOS DE INFORMÁTICA',
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
                'optanteMei': False
            }
        
        return JsonResponse({
            'success': True,
            **dados
        })
    except Exception as e:
        logger.error(f"Erro ao consultar dados na Receita: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Erro ao consultar dados: {str(e)}'
        })

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