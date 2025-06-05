# gestor/views/__init__.py

from .dashboard import home, dashboard
from .cliente import (
    cliente_list, cliente_create, cliente_update, cliente_delete, 
    cliente_detail, cliente_detail_by_codigo
)
from .cliente_contato import (
    cliente_contato_create, cliente_contato_update, cliente_contato_delete
)
from .loja import (
    loja_list, loja_create, loja_edit, loja_delete, 
    loja_detail, loja_update
)
from .vendedor import (
    vendedor_list, vendedor_create, vendedor_edit, vendedor_delete,
    vendedor_detail, vendedor_update
)
from .fabricante import (
    fabricante_list, fabricante_create, fabricante_edit, fabricante_delete,
    fabricante_detail, fabricante_update
)
from .grupo_produto import (
    grupo_list, grupo_create, grupo_edit, grupo_delete,
    grupo_produto_list, grupo_produto_create, grupo_produto_detail,
    grupo_produto_update, grupo_produto_delete
)
from .produto import (
    produto_list, produto_create, produto_edit, produto_delete,
    produto_detail, produto_update
)
from .vendas import (
    vendas_list, vendas_create, vendas_edit, vendas_delete,
    vendas_detail, vendas_update
)
from .importacao import importar_vendas
from .sincronizacao import (
    sincronizacao_dashboard, sincronizar_bi, sincronizar_receita,
    sincronizacao_completa
)
from .usuario import (
    usuario_list, usuario_create, usuario_detail, 
    usuario_update, usuario_delete
)
from .api import (
    api_cliente_por_codigo, api_consultar_receita, vendedor_por_codigo,
    cliente_por_codigo, consultar_receita, consultar_bi
)

__all__ = [
    # Dashboard
    'home', 'dashboard',
    
    # Cliente
    'cliente_list', 'cliente_create', 'cliente_update', 'cliente_delete',
    'cliente_detail', 'cliente_detail_by_codigo',
    
    # Cliente Contato
    'cliente_contato_create', 'cliente_contato_update', 'cliente_contato_delete',
    
    # Loja
    'loja_list', 'loja_create', 'loja_edit', 'loja_delete',
    'loja_detail', 'loja_update',
    
    # Vendedor
    'vendedor_list', 'vendedor_create', 'vendedor_edit', 'vendedor_delete',
    'vendedor_detail', 'vendedor_update',
    
    # Fabricante
    'fabricante_list', 'fabricante_create', 'fabricante_edit', 'fabricante_delete',
    'fabricante_detail', 'fabricante_update',
    
    # Grupo Produto
    'grupo_list', 'grupo_create', 'grupo_edit', 'grupo_delete',
    'grupo_produto_list', 'grupo_produto_create', 'grupo_produto_detail',
    'grupo_produto_update', 'grupo_produto_delete',
    
    # Produto
    'produto_list', 'produto_create', 'produto_edit', 'produto_delete',
    'produto_detail', 'produto_update',
    
    # Vendas
    'vendas_list', 'vendas_create', 'vendas_edit', 'vendas_delete',
    'vendas_detail', 'vendas_update',
    
    # Importação
    'importar_vendas',
    
    # Sincronização
    'sincronizacao_dashboard', 'sincronizar_bi', 'sincronizar_receita',
    'sincronizacao_completa',
    
    # Usuário
    'usuario_list', 'usuario_create', 'usuario_detail',
    'usuario_update', 'usuario_delete',
    
    # APIs
    'api_cliente_por_codigo', 'api_consultar_receita', 'vendedor_por_codigo',
    'cliente_por_codigo', 'consultar_receita', 'consultar_bi',
]