# vendedor/views/cliente.py - VERSÃO SEM FORMSET CNAES

import logging
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Sum, Prefetch
from django.utils import timezone
from django.db import transaction
from django.http import JsonResponse

from core.models import Cliente, ClienteContato, ClienteCnaeSecundario, Vendas, Loja, Vendedor
from core.forms import ClienteForm

logger = logging.getLogger(__name__)


# gestor/views/cliente.py - Função cliente_list atualizada

@login_required
def cliente_list(request):
    """Lista de clientes com filtros aprimorados"""
    # Filtro por tipo de cliente
    tipo_cliente = request.GET.get('tipo', 'principal')  # Default: principal
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
    
    # *** ATUALIZADO: FILTRO POR STATUS COM "OUTROS" ***
    status = request.GET.get('status', 'ativo')  # Default: ativo
    if status == 'ativo':
        clientes_list = clientes_list.filter(status='ativo')
    elif status == 'inativo':
        clientes_list = clientes_list.filter(status='inativo')
    elif status == 'rascunho':
        clientes_list = clientes_list.filter(status='rascunho')
    elif status == 'outros':  # ← NOVA CONDIÇÃO ADICIONADA
        clientes_list = clientes_list.filter(status='outros')
    
    # Filtro por vendedor
    vendedor_codigo = request.GET.get('vendedor', '')
    if vendedor_codigo:
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
    
    # Prefetch para otimizar CNAEs secundários
    clientes_list = clientes_list.prefetch_related(
        Prefetch('cnaes_secundarios', queryset=ClienteCnaeSecundario.objects.order_by('ordem'))
    ).order_by('nome')
    
    # Paginação
    paginator = Paginator(clientes_list, 15)
    page = request.GET.get('page', 1)
    
    try:
        clientes = paginator.page(page)
    except PageNotAnInteger:
        clientes = paginator.page(1)
    except EmptyPage:
        clientes = paginator.page(paginator.num_pages)
    
    # Buscar dados para os selects
    lojas = Loja.objects.filter(ativo=True).order_by('codigo')
    vendedores = Vendedor.objects.filter(ativo=True).order_by('codigo')
    
    context = {
        'clientes': clientes, 
        'status_filtro': status,
        'tipo_filtro': tipo_cliente,
        'vendedor_filtro': vendedor_codigo,
        'loja_filtro': loja_codigo,
        'query': query,
        'lojas': lojas,
        'vendedores': vendedores,
    }
    
    return render(request, 'gestor/cliente_list.html', context)

@login_required
def cliente_create(request):
    """Criar novo cliente - SEM FORMSET CNAE"""
    
    # *** BUSCAR DADOS INICIAIS ***
    # Verificar se é um sub-cliente sendo criado
    codigo_master = request.GET.get('codigo_master', '')
    initial_data = {}
    cliente_master = None
    
    if codigo_master:
        initial_data = {'codigo_master': codigo_master}
        cliente_master = Cliente.objects.filter(codigo=codigo_master).first()
    
    if request.method == 'POST':
        # *** CRIAR FORMULÁRIO APENAS COM OS DADOS POST ***
        form = ClienteForm(request.POST)
        
        # *** VALIDAÇÃO ***
        form_valid = form.is_valid()
        
        # *** DEBUG: LOG DOS ERROS ***
        if not form_valid:
            logger.error(f"❌ ERROS DO FORM: {form.errors}")
            logger.error(f"❌ ERROS NON_FIELD: {form.non_field_errors()}")
            for field_name, field_errors in form.errors.items():
                logger.error(f"   • Campo {field_name}: {field_errors}")
        
        if form_valid:
            try:
                with transaction.atomic():
                    # Salvar cliente
                    cliente = form.save()
                    
                    # Mensagem de sucesso com info do vendedor
                    msg_vendedor = ""
                    if cliente.codigo_vendedor:
                        nome_vendedor = cliente.nome_vendedor  # Usa a property!
                        if nome_vendedor:
                            msg_vendedor = f" | Vendedor: {cliente.codigo_vendedor} - {nome_vendedor}"
                        else:
                            msg_vendedor = f" | ⚠️ Vendedor {cliente.codigo_vendedor} não encontrado"
                    
                    messages.success(request, 
                        f'✅ Cliente "{cliente.nome}" cadastrado com sucesso!{msg_vendedor}'
                    )
                    
                    return redirect('gestor:cliente_detail', pk=cliente.id)
                    
            except Exception as e:
                logger.error(f"💥 Erro ao salvar cliente: {str(e)}")
                messages.error(request, f"Erro ao salvar: {str(e)}")
        else:
            # *** MENSAGEM DE ERRO ESPECÍFICA ***
            error_count = len(form.errors)
            messages.error(request, f"❌ Corrija os {error_count} erro(s) abaixo e tente novamente")
            
            # *** LOG ADICIONAL PARA DEBUG ***
            logger.warning(f"⚠️ Formulário inválido para cliente. Total de erros: {error_count}")
    else:
        # *** GET REQUEST - FORMULÁRIO VAZIO ***
        form = ClienteForm(initial=initial_data)
    
    # *** CONTEXTO SEM FORMSET ***
    context = {
        'form': form,
        'cliente_master_nome': cliente_master.nome if cliente_master else None,
        
        # *** DEBUG INFO ***
        'debug_info': {
            'form_errors_count': len(form.errors) if hasattr(form, 'errors') else 0,
            'is_post': request.method == 'POST',
            'form_is_bound': form.is_bound if hasattr(form, 'is_bound') else False,
        }
    }
    
    return render(request, 'gestor/cliente_form.html', context)

@login_required
def cliente_update(request, pk):
    """Atualizar cliente existente - SEM FORMSET CNAE"""
    cliente = get_object_or_404(Cliente, pk=pk)
    cliente_master = None
    
    if cliente.codigo_master:
        cliente_master = Cliente.objects.filter(codigo=cliente.codigo_master).first()
    
    if request.method == 'POST':
        # *** CRIAR FORMULÁRIO APENAS COM OS DADOS POST ***
        form = ClienteForm(request.POST, instance=cliente)
        
        # *** VALIDAÇÃO ***
        form_valid = form.is_valid()
        
        # *** DEBUG: LOG DOS ERROS ***
        if not form_valid:
            logger.error(f"❌ ERROS DO FORM (UPDATE): {form.errors}")
            for field_name, field_errors in form.errors.items():
                logger.error(f"   • Campo {field_name}: {field_errors}")
        
        if form_valid:
            try:
                with transaction.atomic():
                    # Salvar cliente
                    cliente = form.save()
                    
                    # Mensagem de sucesso com info do vendedor
                    msg_vendedor = ""
                    if cliente.codigo_vendedor:
                        nome_vendedor = cliente.nome_vendedor  # Usa a property!
                        if nome_vendedor:
                            msg_vendedor = f" | Vendedor: {cliente.codigo_vendedor} - {nome_vendedor}"
                        else:
                            msg_vendedor = f" | ⚠️ Vendedor {cliente.codigo_vendedor} não encontrado"
                    
                    messages.success(request, 
                        f'✅ Cliente "{cliente.nome}" atualizado com sucesso!{msg_vendedor}'
                    )
                    
                    return redirect('gestor:cliente_detail', pk=cliente.id)
                    
            except Exception as e:
                logger.error(f"💥 Erro ao atualizar cliente: {str(e)}")
                messages.error(request, f"Erro ao atualizar: {str(e)}")
        else:
            # *** MENSAGEM DE ERRO ESPECÍFICA ***
            error_count = len(form.errors)
            messages.error(request, f"❌ Corrija os {error_count} erro(s) abaixo e tente novamente")
            
            # *** LOG ADICIONAL PARA DEBUG ***
            logger.warning(f"⚠️ Formulário inválido para cliente {cliente.codigo}. Total de erros: {error_count}")
    else:
        # *** GET REQUEST - FORMULÁRIO COM DADOS EXISTENTES ***
        form = ClienteForm(instance=cliente)
    
    # *** CONTEXTO SEM FORMSET ***
    context = {
        'form': form, 
        'cliente': cliente,
        'cliente_master_nome': cliente_master.nome if cliente_master else None,
        
        # *** INFO ADICIONAL PARA DEBUG ***
        'vendedor_info': {
            'codigo': cliente.codigo_vendedor,
            'nome': cliente.nome_vendedor,  # Property automática!
            'info_completa': cliente.vendedor_info_completa,
            'loja_info': cliente.vendedor_loja_info
        },
        
        # *** DEBUG INFO ***
        'debug_info': {
            'form_errors_count': len(form.errors) if hasattr(form, 'errors') else 0,
            'is_post': request.method == 'POST',
            'form_is_bound': form.is_bound if hasattr(form, 'is_bound') else False,
        }
    }
    
    return render(request, 'gestor/cliente_form.html', context)

@login_required
def cliente_detail(request, pk):
    """Detalhe do cliente - Com CNAEs no detalhe (não no form)"""
    cliente = get_object_or_404(Cliente, pk=pk)
    contatos = cliente.contatos.all()
    
    # Buscar CNAEs secundários - APENAS NO DETALHE
    cnaes_secundarios = cliente.cnaes_secundarios.all().order_by('ordem')
    
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
        'cnaes_secundarios': cnaes_secundarios,  # CNAEs apenas no detalhe
        'clientes_associados': clientes_associados,
        'vendas_recentes': vendas_recentes,
        'total_vendas_recentes': total_vendas_recentes,
        # *** INFO DO VENDEDOR AUTOMÁTICA ***
        'vendedor_info': {
            'codigo': cliente.codigo_vendedor,
            'nome': cliente.nome_vendedor,  # Property automática!
            'info_completa': cliente.vendedor_info_completa,
            'dados_completos': cliente.vendedor_loja_info
        }
    }
    
    return render(request, 'gestor/cliente_detail.html', context)

@login_required
def cliente_delete(request, pk):
    """Deletar cliente"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        cliente_nome = cliente.nome
        cliente.delete()
        messages.success(request, f'Cliente "{cliente_nome}" excluído com sucesso.')
        return redirect('gestor:cliente_list')
    
    context = {
        'cliente': cliente,
        'vendedor_info': cliente.vendedor_info_completa  # Info para confirmação
    }
    
    return render(request, 'gestor/cliente_confirm_delete.html', context)

@login_required
def cliente_detail_by_codigo(request, codigo):
    """View para acessar cliente pelo código"""
    cliente = get_object_or_404(Cliente, codigo=codigo)
    return redirect('gestor:cliente_detail', pk=cliente.id)

# *** VIEWS DE API PARA AJAX ***

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

# *** API FICTÍCIA PARA RECEITA FEDERAL ***
# Esta é uma simulação - você deve implementar a API real

@login_required  
def api_consultar_receita(request, cpf_cnpj):
    """API fictícia para consultar dados na Receita Federal"""
    try:
        # Remove caracteres não numéricos
        documento = ''.join(filter(str.isdigit, cpf_cnpj))
        
        # *** SIMULAÇÃO DE RESPOSTA DA RECEITA ***
        # Em produção, aqui você faria a chamada real para a API da Receita Federal
        dados_simulados = {
            'razaoSocial': 'EMPRESA EXEMPLO LTDA',
            'nomeFantasia': 'Empresa Exemplo',
            'situacaoCadastral': '02',  # Ativa
            'naturezaJuridica': 'Sociedade Empresária Limitada',
            'porteEmpresa': 'ME',
            'dataAbertura': '2020-01-15',
            'cnaeFiscal': '4761003',
            'cnaeFiscalDescricao': 'Comércio varejista de artigos de armarinho',
            'optanteSimples': True,
            'optanteMei': False,
        }
        
        return JsonResponse({
            'success': True,
            'dados': dados_simulados,
            'message': 'Dados consultados com sucesso (simulação)'
        })
        
    except Exception as e:
        logger.error(f"Erro na consulta Receita Federal: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Erro ao consultar dados na Receita Federal'
        })