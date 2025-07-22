# vendedor/views/__init__.py - VERSÃO FINAL

from .dashboard import home, dashboard
from .cliente import (
    cliente_list, cliente_detail, cliente_detail_by_codigo,
    api_vendedor_por_codigo, api_cliente_por_codigo, api_consultar_receita,
    consultar_bi
)
from .vendas import vendas_list, vendas_detail
from .relatorio_clientes import relatorio_clientes
from .api_produtos import api_buscar_produtos

__all__ = [
    'home', 'dashboard',
    'cliente_list', 'cliente_detail', 'cliente_detail_by_codigo',
    'api_vendedor_por_codigo', 'api_cliente_por_codigo', 'api_consultar_receita',
    'consultar_bi',
    'vendas_list', 'vendas_detail',
    'relatorio_clientes', 'api_buscar_produtos',
]