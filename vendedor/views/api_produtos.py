# vendedor/views/api_produtos.py - PARA O RELATÓRIO DE CLIENTES

import json
import logging
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from core.models import Produto, GrupoProduto, Fabricante

logger = logging.getLogger(__name__)

@login_required
@require_http_methods(["GET"])
def api_buscar_produtos(request):
    """
    API para busca de produtos com autocomplete - VENDEDOR
    GET /vendedor/api/buscar-produtos/?q=termo&exclude=cod1,cod2
    """
    try:
        query = request.GET.get('q', '').strip()
        exclude_codes = request.GET.get('exclude', '').strip()
        limit = int(request.GET.get('limit', 10))
        
        logger.info(f"🔍 Busca de produtos (vendedor): query='{query}', exclude='{exclude_codes}', limit={limit}")
        
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
        
        # Query base
        produtos_query = Produto.objects.filter(ativo=True).select_related('grupo', 'fabricante')
        
        # Excluir produtos já selecionados
        if exclude_list:
            produtos_query = produtos_query.exclude(codigo__in=exclude_list)
        
        # Filtro de busca
        search_filter = (
            Q(codigo__icontains=query) |
            Q(descricao__icontains=query)
        )
        
        # Buscar também por grupo se o termo for longo
        if len(query) >= 3:
            search_filter |= Q(grupo__descricao__icontains=query)
            search_filter |= Q(fabricante__descricao__icontains=query)
        
        produtos_query = produtos_query.filter(search_filter)
        
        # Ordenação simples
        produtos_query = produtos_query.order_by('codigo')
        
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
            produtos_data.append(produto_dict)
        
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