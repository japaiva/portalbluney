# gestor/views/utils.py

import logging
import json
import ast
from django.db import transaction

from core.models import ClienteCnaeSecundario

logger = logging.getLogger(__name__)

def parse_cnaes_secundarios(cnaes_string):
    """
    Converte string JSON dos CNAEs secundários em lista de dicionários
    """
    if not cnaes_string or cnaes_string in ['', 'NULL', 'null', '[]']:
        return []
    
    try:
        # Método 1: Tentar JSON padrão
        if cnaes_string.startswith('[') and cnaes_string.endswith(']'):
            try:
                # Corrigir aspas simples para aspas duplas
                cnaes_json = cnaes_string.replace("'", '"')
                cnaes_list = json.loads(cnaes_json)
            except json.JSONDecodeError:
                # Método 2: Usar ast.literal_eval (mais seguro para aspas simples)
                cnaes_list = ast.literal_eval(cnaes_string)
        else:
            return []
        
        # Filtrar CNAEs válidos e normalizar
        cnaes_validos = []
        for i, cnae in enumerate(cnaes_list):
            if isinstance(cnae, dict) and cnae.get('codigo') and cnae.get('codigo') != 0:
                cnaes_validos.append({
                    'codigo': str(cnae['codigo']).strip(),
                    'descricao': str(cnae.get('descricao', '')).strip(),
                    'ordem': i + 1
                })
        
        return cnaes_validos
        
    except Exception as e:
        logger.error(f"Erro ao parsear CNAEs secundários: {cnaes_string[:100]}... - {str(e)}")
        return []

def salvar_cnaes_secundarios(cliente, cnaes_secundarios_string):
    """
    Salva os CNAEs secundários de um cliente
    """
    # Limpar CNAEs secundários existentes
    ClienteCnaeSecundario.objects.filter(cliente=cliente).delete()
    
    # Parsear novos CNAEs
    cnaes_list = parse_cnaes_secundarios(cnaes_secundarios_string)
    
    # Salvar cada CNAE secundário
    cnaes_criados = []
    for cnae_data in cnaes_list:
        cnae_secundario = ClienteCnaeSecundario.objects.create(
            cliente=cliente,
            codigo_cnae=cnae_data['codigo'],
            descricao_cnae=cnae_data['descricao'],
            ordem=cnae_data['ordem']
        )
        cnaes_criados.append(cnae_secundario)
    
    return cnaes_criados