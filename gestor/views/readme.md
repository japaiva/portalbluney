# Estrutura das Views do Gestor

A partir de agora, as views do app `gestor` estão organizadas em módulos separados para melhor manutenibilidade e organização do código.

## Estrutura de Arquivos

```
gestor/views/
├── __init__.py          # Importações centralizadas
├── dashboard.py         # Views do dashboard principal
├── cliente.py           # CRUD de clientes
├── cliente_contato.py   # Gerenciamento de contatos
├── loja.py             # CRUD de lojas
├── vendedor.py         # CRUD de vendedores
├── fabricante.py       # CRUD de fabricantes
├── grupo_produto.py    # CRUD de grupos de produto
├── produto.py          # CRUD de produtos
├── vendas.py           # CRUD de vendas
├── importacao.py       # Importação de dados do BI
├── sincronizacao.py    # Sincronização com sistemas externos
├── usuario.py          # Gerenciamento de usuários
├── api.py              # APIs e endpoints JSON
├── utils.py            # Funções auxiliares
└── README.md           # Este arquivo
```

## Organização por Funcionalidade

### Dashboard (`dashboard.py`)
- `home()` - Página inicial
- `dashboard()` - Dashboard principal com estatísticas

### Cliente (`cliente.py`)
- `cliente_list()` - Lista com filtros
- `cliente_create()` - Criar novo cliente
- `cliente_update()` - Editar cliente
- `cliente_delete()` - Excluir cliente
- `cliente_detail()` - Detalhes do cliente
- `cliente_detail_by_codigo()` - Busca por código

### Contatos (`cliente_contato.py`)
- `cliente_contato_create()` - Adicionar contato
- `cliente_contato_update()` - Editar contato
- `cliente_contato_delete()` - Excluir contato

### Lojas (`loja.py`)
- CRUD completo de lojas
- `loja_detail()` - Detalhes com vendedores e vendas

### Vendedores (`vendedor.py`)
- CRUD completo de vendedores
- `vendedor_detail()` - Detalhes com vendas recentes

### Fabricantes (`fabricante.py`)
- CRUD completo de fabricantes
- Listagem de produtos por fabricante

### Grupos de Produto (`grupo_produto.py`)
- CRUD completo de grupos
- Aliases para compatibilidade com URLs

### Produtos (`produto.py`)
- CRUD completo de produtos
- Busca por código, descrição, grupo ou fabricante
- Paginação para listas grandes

### Vendas (`vendas.py`)
- CRUD completo de vendas
- Filtros avançados (data, loja, vendedor)
- `vendas_detail()` - Detalhes com vendas relacionadas

### Importação (`importacao.py`)
- `importar_vendas()` - Importação completa do BI
- Suporte a planilhas auxiliares
- Processamento em lote com feedback

### Sincronização (`sincronizacao.py`)
- `sincronizacao_dashboard()` - Dashboard de sync
- Placeholders para funcionalidades futuras

### Usuários (`usuario.py`)
- CRUD completo de usuários do sistema

### APIs (`api.py`)
- `api_cliente_por_codigo()` - Busca cliente via API
- `vendedor_por_codigo()` - Busca vendedor via API
- `consultar_receita()` - Simulação de consulta RF
- `consultar_bi()` - Consulta dados de BI
- `processar_cnaes_receita()` - Processar CNAEs

### Utilitários (`utils.py`)
- `parse_cnaes_secundarios()` - Parser de CNAEs
- `salvar_cnaes_secundarios()` - Salvar CNAEs no BD

## Importações

O arquivo `__init__.py` centraliza todas as importações, mantendo compatibilidade com o código existente. Todas as views continuam acessíveis da mesma forma:

```python
from gestor.views import cliente_list, cliente_create, dashboard
```

## Vantagens da Nova Estrutura

1. **Organização**: Cada módulo tem responsabilidade específica
2. **Manutenibilidade**: Mais fácil encontrar e editar código
3. **Reutilização**: Funções auxiliares separadas em `utils.py`
4. **Escalabilidade**: Fácil adicionar novas funcionalidades
5. **Compatibilidade**: Mantém todas as importações existentes

## Migração do Código Original

O arquivo original `gestor/views.py` pode ser removido após confirmar que todas as views estão funcionando corretamente com a nova estrutura modular.

## Padrões Utilizados

- **Logging**: Todas as views usam logging adequado
- **Decorators**: `@login_required` em todas as views protegidas
- **Messages**: Feedback consistente para o usuário
- **Exception Handling**: Tratamento de erros robusto
- **Transactions**: Operações atômicas quando necessário
- **Paginação**: Para listas grandes de dados