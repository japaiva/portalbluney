# gestor/views/api.py - VERSÃO CORRIGIDA

import logging
from datetime import timedelta, datetime
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count
from django.db import transaction

from core.models import Cliente, Vendedor, Vendas, ClienteCnaeSecundario

logger = logging.getLogger(__name__)

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
def vendedor_por_codigo(request, codigo):
    """API para buscar vendedor por código - CORRIGIDA"""
    try:
        # Garantir que o código tem 3 dígitos
        codigo_formatado = str(codigo).zfill(3)
        vendedor = Vendedor.objects.get(codigo=codigo_formatado, ativo=True)
        
        return JsonResponse({
            'success': True,
            'codigo': vendedor.codigo,
            'nome': vendedor.nome,
            'loja': vendedor.loja.nome if vendedor.loja else None,
            'loja_codigo': vendedor.loja.codigo if vendedor.loja else None
        })
    except Vendedor.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': f'Vendedor com código {codigo} não encontrado'
        })
    except Exception as e:
        logger.error(f"Erro ao buscar vendedor {codigo}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        })

@login_required
def cliente_por_codigo(request, codigo):
    """API para buscar cliente por código - CORRIGIDA"""
    try:
        cliente = Cliente.objects.get(codigo=codigo)
        return JsonResponse({
            'success': True,
            'codigo': cliente.codigo,
            'nome': cliente.nome,
            'status': cliente.get_status_display()
        })
    except Cliente.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': f'Cliente com código {codigo} não encontrado'
        })
    except Exception as e:
        logger.error(f"Erro ao buscar cliente {codigo}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Erro interno: {str(e)}'
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

@login_required
def consultar_receita(request, cpf_cnpj):
    """API para consultar dados na Receita Federal - MELHORADA"""
    # Remove caracteres não numéricos
    documento = ''.join(filter(str.isdigit, cpf_cnpj))
    
    try:
        if len(documento) == 14:  # CNPJ
            # Simulação de dados da Receita Federal para CNPJ
            dados = {
                'razaoSocial': 'EMPRESA EXEMPLO LTDA',
                'nomeFantasia': 'Empresa Exemplo',
                'situacaoCadastral': '02',  # Código que será normalizado
                'dataSituacaoCadastral': '2020-01-01',
                'motivoSituacaoCadastral': 'SEM MOTIVO',
                'naturezaJuridica': '206-2 - SOCIEDADE EMPRESÁRIA LIMITADA',
                'porteEmpresa': 'MICRO EMPRESA',
                'dataAbertura': '2020-01-01',
                'cnaeFiscal': '4761003',
                'cnaeFiscalDescricao': 'Comércio varejista de artigos do vestuário e acessórios',
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
                'cnaesSecundarios': [
                    {
                        'codigo': '4789005',
                        'descricao': 'Comércio varejista de outros produtos não especificados anteriormente'
                    },
                    {
                        'codigo': '4751201',
                        'descricao': 'Comércio varejista especializado de equipamentos e suprimentos de informática'
                    },
                    {
                        'codigo': '6201501',
                        'descricao': 'Desenvolvimento de programas de computador sob encomenda'
                    }
                ]
            }
            
            return JsonResponse({
                'success': True,
                'dados': dados
            })
            
        elif len(documento) == 11:  # CPF
            # Simulação de dados da Receita Federal para CPF
            dados = {
                'razaoSocial': 'JOÃO DA SILVA',
                'nomeFantasia': '',
                'situacaoCadastral': '02',  # Ativa
                'dataSituacaoCadastral': '2020-01-01',
                'motivoSituacaoCadastral': 'SEM MOTIVO',
                'naturezaJuridica': 'PESSOA FÍSICA',
                'porteEmpresa': '',
                'dataAbertura': '',
                'cnaeFiscal': '',
                'cnaeFiscalDescricao': '',
                'optanteSimples': False,
                'optanteMei': False,
                'cnaesSecundarios': []
            }
            
            return JsonResponse({
                'success': True,
                'dados': dados
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'CPF/CNPJ deve ter 11 ou 14 dígitos'
            })
            
    except Exception as e:
        logger.error(f"Erro ao consultar Receita Federal para {cpf_cnpj}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Erro ao consultar dados: {str(e)}'
        })

# ===== VIEW DE CONSULTA BI - CORRIGIDA =====

@login_required
def consultar_bi(request, codigo):
    """
    View para consultar dados de BI (vendas) do cliente - CORRIGIDA
    """
    cliente = get_object_or_404(Cliente, codigo=codigo)
    
    # Parâmetros de filtro
    filtro_periodo = request.GET.get('periodo', '90')  # Default: últimos 90 dias
    data_inicio_param = request.GET.get('data_inicio')
    data_fim_param = request.GET.get('data_fim')
    format_response = request.GET.get('format', 'html')  # html ou json
    
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
    if not cliente.codigo_master and cliente.is_cliente_principal():
        # Se é cliente principal, incluir sub-clientes
        sub_clientes = cliente.get_sub_clientes()
        if sub_clientes:
            codigos_clientes.extend([c.codigo for c in sub_clientes])
    
    # Buscar vendas no período - *** CORRIGIDO: REMOVIDO 'vendedor' ***
    try:
        vendas = Vendas.objects.filter(
            cliente__codigo__in=codigos_clientes,
            data_venda__gte=data_inicio,
            data_venda__lte=data_fim
        ).select_related(
            'produto', 'loja', 'grupo_produto', 'fabricante', 'cliente'
            # ❌ REMOVIDO: 'vendedor' - não existe mais no modelo!
            # ✅ vendedor_nf é CharField, não precisa de select_related
        ).order_by('-data_venda')
        
        # Calcular totais
        totais = vendas.aggregate(
            total_valor=Sum('valor_total'),
            total_quantidade=Sum('quantidade'),
            total_vendas=Count('id')
        )
        
        total_valor = totais['total_valor'] or 0
        total_quantidade = totais['total_quantidade'] or 0
        total_vendas = totais['total_vendas'] or 0
        
        # Limitar vendas para exibição (máximo 1000 registros)
        vendas_limitadas = vendas[:1000] if vendas.count() > 1000 else vendas
        
    except Exception as e:
        logger.error(f"Erro ao consultar dados de BI para cliente {codigo}: {str(e)}")
        vendas = Vendas.objects.none()
        vendas_limitadas = vendas
        total_valor = 0
        total_quantidade = 0
        total_vendas = 0
    
    # Resposta JSON para APIs
    if format_response == 'json':
        vendas_data = []
        for venda in vendas_limitadas:
            # *** CORRIGIDO: USAR vendedor_nf e vendedor_nf_nome ***
            vendas_data.append({
                'data_venda': venda.data_venda.strftime('%Y-%m-%d'),
                'produto_codigo': venda.produto.codigo,
                'produto_descricao': venda.produto.descricao,
                'loja_codigo': venda.loja.codigo,
                'loja_nome': venda.loja.nome,
                'vendedor_codigo': venda.vendedor_nf or '',  # ← CORRIGIDO
                'vendedor_nome': venda.vendedor_nf_nome or '',  # ← CORRIGIDO: usar property
                'quantidade': float(venda.quantidade),
                'valor_total': float(venda.valor_total),
                'numero_nf': venda.numero_nf or '',
                'serie_nf': venda.serie_nf or '',
                'grupo_produto': venda.grupo_produto.descricao if venda.grupo_produto else '',
                'fabricante': venda.fabricante.descricao if venda.fabricante else '',
                'cliente_codigo': venda.cliente.codigo,
                'cliente_nome': venda.cliente.nome,
            })
        
        response_data = {
            'cliente': {
                'codigo': cliente.codigo,
                'nome': cliente.nome,
                'nome_fantasia': cliente.nome_fantasia or '',
                'cpf_cnpj': cliente.cpf_cnpj or '',
                'status': cliente.status,
            },
            'periodo': {
                'data_inicio': data_inicio.strftime('%Y-%m-%d'),
                'data_fim': data_fim.strftime('%Y-%m-%d'),
                'filtro_periodo': filtro_periodo,
            },
            'totais': {
                'total_valor': float(total_valor),
                'total_quantidade': float(total_quantidade),
                'total_vendas': total_vendas,
                'ticket_medio': float(total_valor / total_vendas) if total_vendas > 0 else 0,
            },
            'vendas': vendas_data,
            'meta': {
                'total_registros': vendas.count(),
                'registros_exibidos': len(vendas_data),
                'limitado': vendas.count() > 1000,
            }
        }
        
        return JsonResponse(response_data, safe=False)
    
    # Resposta HTML (template)
    context = {
        'cliente': cliente,
        'vendas': vendas_limitadas,
        'total_valor': total_valor,
        'total_quantidade': total_quantidade,
        'total_vendas': total_vendas,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'filtro_periodo': filtro_periodo,
        
        # Meta informações
        'total_registros': vendas.count(),
        'registros_limitados': vendas.count() > 1000,
        
        # Para os gráficos JavaScript - *** CORRIGIDO ***
        'vendas_json': list(vendas_limitadas.values(
            'data_venda', 'produto__descricao', 'valor_total', 'vendedor_nf'  # ← CORRIGIDO
        )),
        
        # *** INFO ADICIONAL PARA DEBUG ***
        'debug_info': {
            'codigos_clientes': codigos_clientes,
            'total_vendas_query': vendas.count(),
            'vendas_limitadas': len(vendas_limitadas),
        }
    }
    
    return render(request, 'gestor/cliente_bi.html', context)

# ===== UTILITÁRIOS =====

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