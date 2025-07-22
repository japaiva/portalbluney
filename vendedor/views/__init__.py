# vendedor/views/__init__.py

# Importar todas as views do módulo vendedor baseado nos arquivos existentes

from .dashboard import dashboard
from .cliente import (
    cliente_list as listar_clientes, 
    cliente_detail as detalhar_cliente, 
    cliente_update as editar_cliente
)
from .cliente_contato import (
    cliente_contato_create as listar_contatos,  # Adapter
    cliente_contato_create as adicionar_contato,
    cliente_contato_update as editar_contato,
    cliente_contato_delete as deletar_contato
)
from .vendas import (
    vendas_list as historico_vendas,
    vendas_detail as detalhar_venda
)
from .relatorio_clientes import (
    relatorio_clientes as relatorio_vendas,
    relatorio_clientes as relatorio_clientes_vendedor  # Reutilizando a mesma função
)

# Para adaptar as funções do gestor ao vendedor, vamos criar wrappers
def listar_contatos(request, codigo_cliente):
    """Adapter para listar contatos de um cliente"""
    from django.shortcuts import get_object_or_404
    from core.models import Cliente
    
    # Verificar acesso ao cliente
    if request.user.codigo_vendedor:
        cliente = get_object_or_404(
            Cliente, 
            codigo=codigo_cliente,
            codigo_vendedor=request.user.codigo_vendedor
        )
    else:
        cliente = get_object_or_404(Cliente, codigo=codigo_cliente)
    
    # Buscar contatos
    contatos = cliente.contatos.all().order_by('-principal', 'nome')
    
    # Registrar consulta para auditoria
    from ..models import ConsultaCliente
    ConsultaCliente.objects.create(
        vendedor=request.user,
        cliente=cliente,
        tipo_consulta='contato'
    )
    
    from django.shortcuts import render
    context = {
        'cliente': cliente,
        'contatos': contatos,
    }
    
    return render(request, 'vendedor/contatos/listar.html', context)

__all__ = [
    # Dashboard
    'dashboard',
    
    # Cliente
    'listar_clientes', 'detalhar_cliente', 'editar_cliente',
    
    # Contatos
    'listar_contatos', 'adicionar_contato', 'editar_contato', 'deletar_contato',
    
    # Vendas
    'historico_vendas', 'detalhar_venda',
    
    # Relatórios
    'relatorio_vendas', 'relatorio_clientes_vendedor',
]