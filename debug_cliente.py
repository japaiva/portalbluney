#!/usr/bin/env python
"""
Script para debug completo do cliente 93278 (Viana)
"""

import os
import sys
import django

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalcomercial.settings')
    django.setup()

import pandas as pd
from core.models import Cliente

def main():
    print("🔍 DEBUG COMPLETO - Cliente 93278 (VIANA)...")
    
    # 1. Verificar se existe no banco com diferentes variações
    print("\n1️⃣ VERIFICAÇÃO NO BANCO DE DADOS:")
    
    # Buscar por código exato
    print("   🔸 Busca por código '93278':")
    cliente_93278 = Cliente.objects.filter(codigo='93278').first()
    if cliente_93278:
        print(f"      ✅ ENCONTRADO: {cliente_93278.codigo} - {cliente_93278.nome}")
        print(f"         Ativo: {cliente_93278.ativo}")
        print(f"         Código Master: {cliente_93278.codigo_master}")
        print(f"         CPF/CNPJ: {cliente_93278.cpf_cnpj}")
        return cliente_93278
    else:
        print("      ❌ NÃO encontrado com código '93278'")
    
    # Buscar por nome contendo "VIANA"
    print("   🔸 Busca por nome contendo 'VIANA':")
    clientes_viana = Cliente.objects.filter(nome__icontains='VIANA')
    if clientes_viana.exists():
        print(f"      ✅ ENCONTRADOS {clientes_viana.count()} cliente(s) com 'VIANA':")
        for cliente in clientes_viana:
            print(f"         {cliente.codigo} - {cliente.nome} (Ativo: {cliente.ativo})")
    else:
        print("      ❌ NÃO encontrado nenhum cliente com 'VIANA' no nome")
    
    # Buscar por código contendo "93278"
    print("   🔸 Busca por código contendo '93278':")
    clientes_codigo = Cliente.objects.filter(codigo__icontains='93278')
    if clientes_codigo.exists():
        print(f"      ✅ ENCONTRADOS {clientes_codigo.count()} cliente(s) com '93278':")
        for cliente in clientes_codigo:
            print(f"         {cliente.codigo} - {cliente.nome} (Ativo: {cliente.ativo})")
    else:
        print("      ❌ NÃO encontrado nenhum cliente com '93278' no código")
    
    # Buscar por CNPJ
    print("   🔸 Busca por CNPJ '12137817000195':")
    cliente_cnpj = Cliente.objects.filter(cpf_cnpj='12137817000195').first()
    if cliente_cnpj:
        print(f"      ✅ ENCONTRADO por CNPJ: {cliente_cnpj.codigo} - {cliente_cnpj.nome}")
        return cliente_cnpj
    else:
        print("      ❌ NÃO encontrado por CNPJ")
    
    # 2. Verificar total de clientes no banco
    print("\n2️⃣ ESTATÍSTICAS DO BANCO:")
    total_clientes = Cliente.objects.count()
    clientes_ativos = Cliente.objects.filter(ativo=True).count()
    clientes_inativos = Cliente.objects.filter(ativo=False).count()
    print(f"   📊 Total de clientes: {total_clientes}")
    print(f"   📊 Clientes ativos: {clientes_ativos}")
    print(f"   📊 Clientes inativos: {clientes_inativos}")
    
    # 3. Listar alguns códigos próximos
    print("\n3️⃣ CÓDIGOS PRÓXIMOS A 93278:")
    for codigo in ['93270', '93275', '93276', '93277', '93278', '93279', '93280', '93285']:
        cliente = Cliente.objects.filter(codigo=codigo).first()
        if cliente:
            print(f"   ✅ {codigo}: {cliente.nome}")
        else:
            print(f"   ❌ {codigo}: NÃO ENCONTRADO")
    
    # 4. Verificar se está nos arquivos de origem
    print("\n4️⃣ VERIFICAÇÃO NOS ARQUIVOS:")
    
    # LISTARE
    if os.path.exists('listare.xlsx'):
        print("   📖 Verificando LISTARE...")
        df_listare = pd.read_excel('listare.xlsx')
        viana_listare = df_listare[
            (df_listare.get('CODIGO', pd.Series()) == 93278) | 
            (df_listare.get('codcli', pd.Series()) == 93278) |
            (df_listare['NOME'].str.contains('VIANA', case=False, na=False))
        ]
        if not viana_listare.empty:
            print(f"      ✅ ENCONTRADO no LISTARE: {len(viana_listare)} registro(s)")
            for idx, row in viana_listare.iterrows():
                codigo = row.get('CODIGO', row.get('codcli'))
                print(f"         Linha {idx}: {codigo} - {row['NOME']}")
        else:
            print("      ❌ NÃO encontrado no LISTARE")
    
    # CLIENTEs
    if os.path.exists('CLIENTEs.xlsx'):
        print("   📖 Verificando CLIENTEs...")
        df_clientes = pd.read_excel('CLIENTEs.xlsx')
        print(f"      📋 Colunas disponíveis: {list(df_clientes.columns)}")
        
        # Tentar diferentes colunas
        colunas_codigo = ['CODCLI', 'codcli', 'codigo', 'CODIGO']
        encontrado = False
        
        for col in colunas_codigo:
            if col in df_clientes.columns:
                viana_clientes = df_clientes[df_clientes[col] == 93278]
                if not viana_clientes.empty:
                    print(f"      ✅ ENCONTRADO no CLIENTEs (coluna {col}): {len(viana_clientes)} registro(s)")
                    encontrado = True
                    break
        
        if not encontrado:
            print("      ❌ NÃO encontrado no CLIENTEs")
    
    # CSV
    if os.path.exists('clientes.csv'):
        print("   📖 Verificando clientes.csv...")
        df_csv = pd.read_csv('clientes.csv')
        viana_csv = df_csv[df_csv['codigo'] == 93278]
        if not viana_csv.empty:
            print("      ✅ ENCONTRADO no CSV:")
            row = viana_csv.iloc[0]
            print(f"         {row['codigo']} - {row['nome']}")
            print(f"         Ativo: {row['ativo']}")
            print(f"         CNPJ: {row['cpf_cnpj']}")
            
            # Oferecer importação
            print("\n💡 CLIENTE ESTÁ NO CSV MAS NÃO NO BANCO!")
            resposta = input("Deseja importar este cliente agora? (s/n): ")
            if resposta.lower() == 's':
                importar_cliente_csv(row)
        else:
            print("      ❌ NÃO encontrado no CSV")
    
    # 5. Testar a busca da view
    print("\n5️⃣ TESTE DA BUSCA DA VIEW:")
    
    # Simular a busca que acontece na view cliente_list
    from django.db.models import Q
    
    query_tests = ['93278', 'VIANA', 'viana', 'Viana', 'CORREA']
    
    for query in query_tests:
        print(f"   🔍 Testando busca: '{query}'")
        clientes_busca = Cliente.objects.filter(
            Q(nome__icontains=query) | 
            Q(codigo__icontains=query) |
            Q(cpf_cnpj__icontains=query)
        )
        
        if clientes_busca.exists():
            print(f"      ✅ ENCONTRADOS {clientes_busca.count()} resultado(s):")
            for cliente in clientes_busca[:5]:  # Mostrar só os primeiros 5
                print(f"         {cliente.codigo} - {cliente.nome}")
        else:
            print(f"      ❌ Nenhum resultado para '{query}'")
    
    print("\n6️⃣ RECOMENDAÇÕES:")
    if not Cliente.objects.filter(codigo='93278').exists():
        print("   🔧 Cliente 93278 NÃO está no banco")
        print("   💡 Soluções:")
        print("      1. Verificar se estava no LISTARE original")
        print("      2. Importar manualmente do CSV")
        print("      3. Verificar logs de importação")
    else:
        print("   ✅ Cliente está no banco - problema pode ser na interface")

def importar_cliente_csv(row):
    """Importa cliente específico do CSV"""
    from django.utils import timezone
    import re
    
    print("\n🚀 Importando cliente do CSV...")
    
    try:
        dados = {
            'codigo': str(row['codigo']),
            'nome': row['nome'],
            'ativo': bool(row['ativo']),
            'data_cadastro': timezone.now(),
            'cpf_cnpj': str(row['cpf_cnpj']).replace('.0', '') if pd.notna(row['cpf_cnpj']) else None,
            'cidade': row.get('cidade') if pd.notna(row.get('cidade')) else None,
            'estado': row.get('estado') if pd.notna(row.get('estado')) else None,
            'endereco': row.get('endereco') if pd.notna(row.get('endereco')) else None,
            'tipo_documento': 'cnpj' if len(str(row['cpf_cnpj']).replace('.0', '')) > 11 else 'cpf'
        }
        
        cliente = Cliente.objects.create(**dados)
        print(f"✅ SUCESSO! Cliente importado: {cliente.codigo} - {cliente.nome}")
        
        # Verificar se agora aparece na busca
        print("\n🔍 Testando busca após importação...")
        busca_resultado = Cliente.objects.filter(codigo='93278').first()
        if busca_resultado:
            print(f"✅ Cliente agora encontrado na busca: {busca_resultado.nome}")
        
    except Exception as e:
        print(f"❌ ERRO ao importar: {str(e)}")

if __name__ == "__main__":
    main()