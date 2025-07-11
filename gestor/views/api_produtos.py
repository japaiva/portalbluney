# gestor/views/api_produtos.py
# API Views para busca de produtos com tags - VERSÃO CORRIGIDA

import json
import logging
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Case, When, IntegerField
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from core.models import Produto, GrupoProduto, Fabricante

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def buscar_produtos_api(request):
    """
    API para busca de produtos com autocomplete
    GET /api/produtos/buscar/?q=termo&exclude=cod1,cod2
    """
    try:
        query = request.GET.get('q', '').strip()
        exclude_codes = request.GET.get('exclude', '').strip()
        limit = int(request.GET.get('limit', 10))
        
        logger.info(f"🔍 Busca de produtos: query='{query}', exclude='{exclude_codes}', limit={limit}")
        
        # Validações
        if not query or len(query) < 2:
            return JsonResponse({
                'success': False,
                'message': 'Termo de busca deve ter pelo menos 2 caracteres',
                'produtos': []
            })
        
        # Códigos a excluir
        exclude_list = []
        if exclude_codes:
            exclude_list = [code.strip() for code in exclude_codes.split(',') if code.strip()]
            logger.info(f"📝 Excluindo códigos: {exclude_list}")
        
        # Query base - usando os modelos do seu projeto
        produtos_query = Produto.objects.filter(ativo=True).select_related('grupo', 'fabricante')
        
        # Excluir produtos já selecionados
        if exclude_list:
            produtos_query = produtos_query.exclude(codigo__in=exclude_list)
        
        # Filtro de busca (código, descrição)
        search_filter = (
            Q(codigo__icontains=query) |
            Q(descricao__icontains=query)
        )
        
        # Buscar também por grupo se o termo for longo
        if len(query) >= 3:
            search_filter |= Q(grupo__descricao__icontains=query)
            # Adicionar busca por fabricante também
            search_filter |= Q(fabricante__descricao__icontains=query)
        
        produtos_query = produtos_query.filter(search_filter)
        
        # *** CORREÇÃO: Ordenação sem ambiguidade ***
        # Usando Case/When em vez de extra() para evitar ambiguidade de colunas
        produtos_query = produtos_query.annotate(
            # Prioridade 1: Código que começa com o termo (0 = maior prioridade)
            starts_with_code=Case(
                When(codigo__istartswith=query, then=0),
                default=1,
                output_field=IntegerField()
            ),
            # Prioridade 2: Nome que começa com o termo
            starts_with_name=Case(
                When(descricao__istartswith=query, then=0),
                default=1,
                output_field=IntegerField()
            ),
            # Prioridade 3: Código contém o termo
            contains_code=Case(
                When(codigo__icontains=query, then=0),
                default=1,
                output_field=IntegerField()
            )
        ).order_by(
            'starts_with_code',
            'starts_with_name', 
            'contains_code',
            'codigo'  # Aqui não há ambiguidade pois é o último nível
        )
        
        # Limitar resultados
        produtos = produtos_query[:limit]
        
        logger.info(f"📦 Encontrados {len(produtos)} produtos")
        
        # Serializar dados
        produtos_data = []
        for produto in produtos:
            produto_dict = {
                'codigo': produto.codigo,
                'descricao': produto.descricao,
                'grupo': produto.grupo.descricao if produto.grupo else None,
                'grupo_codigo': produto.grupo.codigo if produto.grupo else None,
                'fabricante': produto.fabricante.descricao if produto.fabricante else None,
                'fabricante_codigo': produto.fabricante.codigo if produto.fabricante else None,
                'ativo': produto.ativo,
            }
            
            # Adicionar preço se existir
            if hasattr(produto, 'preco') and produto.preco:
                produto_dict['preco'] = float(produto.preco)
            else:
                produto_dict['preco'] = None
            
            produtos_data.append(produto_dict)
        
        logger.info(f"✅ Busca concluída com sucesso: {len(produtos_data)} produtos retornados")
        
        return JsonResponse({
            'success': True,
            'produtos': produtos_data,
            'total': len(produtos_data),
            'query': query
        })
        
    except Exception as e:
        logger.error(f"❌ Erro na busca de produtos: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'Erro interno do servidor: {str(e)}',
            'produtos': []
        }, status=500)


@login_required
@require_http_methods(["GET"])
def produto_detail_api(request, codigo):
    """
    API para obter dados completos de um produto específico
    GET /api/produtos/{codigo}/
    """
    try:
        produto = Produto.objects.select_related('grupo', 'fabricante').get(
            codigo=codigo, 
            ativo=True
        )
        
        produto_data = {
            'codigo': produto.codigo,
            'descricao': produto.descricao,
            'grupo': produto.grupo.descricao if produto.grupo else None,
            'grupo_codigo': produto.grupo.codigo if produto.grupo else None,
            'fabricante': produto.fabricante.descricao if produto.fabricante else None,
            'fabricante_codigo': produto.fabricante.codigo if produto.fabricante else None,
            'ativo': produto.ativo,
        }
        
        # Adicionar preço se existir
        if hasattr(produto, 'preco') and produto.preco:
            produto_data['preco'] = float(produto.preco)
        else:
            produto_data['preco'] = None
        
        return JsonResponse({
            'success': True,
            'produto': produto_data
        })
        
    except Produto.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Produto não encontrado'
        }, status=404)
    except Exception as e:
        logger.error(f"❌ Erro ao buscar produto {codigo}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Erro interno do servidor'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def produtos_lista_api(request):
    """
    API para obter lista de produtos por códigos
    POST /api/produtos/lista/
    Body: {"codigos": ["001", "002", "003"]}
    """
    try:
        data = json.loads(request.body)
        codigos = data.get('codigos', [])
        
        if not codigos:
            return JsonResponse({
                'success': False,
                'message': 'Lista de códigos é obrigatória',
                'produtos': []
            })
        
        produtos = Produto.objects.filter(
            codigo__in=codigos,
            ativo=True
        ).select_related('grupo', 'fabricante')
        
        produtos_data = []
        for produto in produtos:
            produto_dict = {
                'codigo': produto.codigo,
                'descricao': produto.descricao,
                'grupo': produto.grupo.descricao if produto.grupo else None,
                'grupo_codigo': produto.grupo.codigo if produto.grupo else None,
                'fabricante': produto.fabricante.descricao if produto.fabricante else None,
                'fabricante_codigo': produto.fabricante.codigo if produto.fabricante else None,
                'ativo': produto.ativo,
            }
            
            # Adicionar preço se existir
            if hasattr(produto, 'preco') and produto.preco:
                produto_dict['preco'] = float(produto.preco)
            else:
                produto_dict['preco'] = None
            
            produtos_data.append(produto_dict)
        
        return JsonResponse({
            'success': True,
            'produtos': produtos_data,
            'total': len(produtos_data)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'JSON inválido'
        }, status=400)
    except Exception as e:
        logger.error(f"❌ Erro na lista de produtos: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Erro interno do servidor'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def grupos_produtos_api(request):
    """
    API para listar grupos de produtos
    GET /api/grupos-produtos/
    """
    try:
        grupos = GrupoProduto.objects.filter(ativo=True).order_by('codigo')
        
        grupos_data = []
        for grupo in grupos:
            grupos_data.append({
                'codigo': grupo.codigo,
                'descricao': grupo.descricao,
                'ativo': grupo.ativo
            })
        
        return JsonResponse({
            'success': True,
            'grupos': grupos_data,
            'total': len(grupos_data)
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar grupos: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Erro interno do servidor'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def fabricantes_api(request):
    """
    API para listar fabricantes
    GET /api/fabricantes/
    """
    try:
        fabricantes = Fabricante.objects.filter(ativo=True).order_by('codigo')
        
        fabricantes_data = []
        for fabricante in fabricantes:
            fabricantes_data.append({
                'codigo': fabricante.codigo,
                'descricao': fabricante.descricao,
                'ativo': fabricante.ativo
            })
        
        return JsonResponse({
            'success': True,
            'fabricantes': fabricantes_data,
            'total': len(fabricantes_data)
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar fabricantes: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Erro interno do servidor'
        }, status=500)


# ===== API AUXILIAR PARA DEBUG =====
@login_required
@require_http_methods(["GET"])
def debug_produtos_api(request):
    """
    API para debug - retorna informações sobre a estrutura dos produtos
    GET /api/produtos/debug/
    """
    try:
        # Contar produtos
        total_produtos = Produto.objects.count()
        produtos_ativos = Produto.objects.filter(ativo=True).count()
        
        # Amostrar alguns produtos
        sample_produtos = list(
            Produto.objects.filter(ativo=True)
            .select_related('grupo', 'fabricante')[:5]
            .values(
                'codigo', 'descricao', 'ativo',
                'grupo__codigo', 'grupo__descricao',
                'fabricante__codigo', 'fabricante__descricao'
            )
        )
        
        # Verificar relacionamentos
        produtos_sem_grupo = Produto.objects.filter(grupo__isnull=True).count()
        produtos_sem_fabricante = Produto.objects.filter(fabricante__isnull=True).count()
        
        return JsonResponse({
            'success': True,
            'debug_info': {
                'total_produtos': total_produtos,
                'produtos_ativos': produtos_ativos,
                'produtos_sem_grupo': produtos_sem_grupo,
                'produtos_sem_fabricante': produtos_sem_fabricante,
                'sample_produtos': sample_produtos,
                'database_tables': {
                    'produto_table': Produto._meta.db_table,
                    'grupo_table': GrupoProduto._meta.db_table,
                    'fabricante_table': Fabricante._meta.db_table,
                }
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Erro no debug: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Erro no debug: {str(e)}'
        }, status=500)