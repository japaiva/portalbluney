#!/usr/bin/env python
"""
Teste da correção da importação da Receita Federal
"""

import os
import sys
import django

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalcomercial.settings')
    django.setup()

import pandas as pd
import re
from core.models import Cliente

def limpar_cpf_cnpj(documento):
    """Remove caracteres não numéricos do CPF/CNPJ e formata"""
    if pd.isna(documento):
        return None
    
    if isinstance(documento, float):
        doc_str = str(int(documento))
    else:
        doc_str = str(documento)
    
    doc_str = re.sub(r'\D', '', doc_str)
    
    if len(doc_str) < 11:
        return None
    elif len(doc_str) == 11:
        return doc_str  # CPF
    elif len(doc_str) <= 14:
        return doc_str.zfill(14)  # CNPJ com zeros à esquerda
    
    return doc_str[:14]

def main():
    print("🔧 TESTE DA CORREÇÃO - Receita Federal...")
    
    # Carregar dados da Receita com correção
    print("\n📖 Carregando receita.xlsx (CORRIGIDO)...")
    df_receita = pd.read_excel('receita.xlsx')
    print(f"   📊 {len(df_receita)} registros carregados")
    
    # Indexar corretamente pela coluna 'cnpj'
    print("\n🔄 Indexando pela coluna 'cnpj'...")
    receita_dict = {}
    
    for index, row in df_receita.iterrows():
        cpf_cnpj_limpo = limpar_cpf_cnpj(row.get('cnpj'))
        if cpf_cnpj_limpo:
            receita_dict[cpf_cnpj_limpo] = row.to_dict()
    
    print(f"   ✅ {len(receita_dict)} registros indexados com sucesso!")
    print(f"   📊 Taxa de sucesso: {len(receita_dict)/len(df_receita)*100:.1f}%")
    
    # Verificar correspondências com clientes
    print(f"\n🔗 VERIFICANDO CORRESPONDÊNCIA COM CLIENTES:")
    clientes_com_cpf = Cliente.objects.exclude(cpf_cnpj__isnull=True).exclude(cpf_cnpj='')
    print(f"   📊 {clientes_com_cpf.count()} clientes têm CPF/CNPJ")
    
    matches = 0
    exemplos_match = []
    
    for cliente in clientes_com_cpf:
        cpf_cnpj_cliente = limpar_cpf_cnpj(cliente.cpf_cnpj)
        if cpf_cnpj_cliente and cpf_cnpj_cliente in receita_dict:
            matches += 1
            if len(exemplos_match) < 5:
                exemplos_match.append({
                    'codigo': cliente.codigo,
                    'nome': cliente.nome,
                    'cpf_cnpj': cliente.cpf_cnpj
                })
    
    print(f"   ✅ {matches} clientes têm correspondência na Receita!")
    print(f"   📊 Taxa de correspondência: {matches/clientes_com_cpf.count()*100:.1f}%")
    
    if exemplos_match:
        print(f"\n📝 EXEMPLOS DE CORRESPONDÊNCIAS:")
        for exemplo in exemplos_match:
            print(f"      {exemplo['codigo']} - {exemplo['nome']} ({exemplo['cpf_cnpj']})")
    
    # Teste específico com clientes conhecidos
    print(f"\n🎯 TESTE COM CLIENTES CONHECIDOS:")
    clientes_teste = ['93278', '88641', '1000']  # VIANA, EMANUEL, etc.
    
    for codigo in clientes_teste:
        cliente = Cliente.objects.filter(codigo=codigo).first()
        if cliente and cliente.cpf_cnpj:
            cpf_cnpj_limpo = limpar_cpf_cnpj(cliente.cpf_cnpj)
            tem_receita = cpf_cnpj_limpo in receita_dict if cpf_cnpj_limpo else False
            status = "✅ TEM" if tem_receita else "❌ NÃO TEM"
            print(f"      {codigo} - {cliente.nome}: {status} dados na Receita")
        else:
            print(f"      {codigo}: Cliente não encontrado ou sem CPF/CNPJ")
    
    print(f"\n💡 CONCLUSÃO:")
    if matches > 0:
        print("   ✅ Correção funcionou! Agora conseguimos mapear dados da Receita")
        print("   🚀 Execute novamente a importação para aplicar os dados da Receita")
    else:
        print("   ⚠️  Ainda há problemas no mapeamento")
        print("   🔍 Verificar se os CPF/CNPJ dos clientes estão no formato correto")

if __name__ == "__main__":
    main()