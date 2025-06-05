# gestor/views/api.py

import logging
from datetime import timedelta
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum
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
            from django.shortcuts import render
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
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.error(request, f'Erro ao consultar dados de BI: {str(e)}')
            return redirect('gestor:cliente_detail', pk=cliente.id)

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