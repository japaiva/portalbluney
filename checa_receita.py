#!/usr/bin/env python
"""
Debug para verificar quais campos estão disponíveis na Receita Federal
"""

import pandas as pd
import os

def main():
    print("🔍 DEBUG - Campos da Receita Federal...")
    
    if not os.path.exists('receita.xlsx'):
        print("❌ Arquivo receita.xlsx não encontrado!")
        return
    
    print("📖 Carregando receita.xlsx...")
    df_receita = pd.read_excel('receita.xlsx')
    print(f"   📊 {len(df_receita)} registros carregados")
    
    # Analisar colunas
    print(f"\n📋 COLUNAS DISPONÍVEIS ({len(df_receita.columns)}):")
    for i, col in enumerate(df_receita.columns, 1):
        print(f"   {i:2d}. {col}")
    
    # Se for apenas uma coluna 'cnpj', vamos verificar se há mais dados
    if len(df_receita.columns) == 1:
        print("\n⚠️  ATENÇÃO: Arquivo receita.xlsx tem apenas 1 coluna!")
        print("   Este arquivo contém apenas os CNPJs, sem dados adicionais da Receita.")
        print("   Para importar dados da Receita Federal, você precisa de um arquivo com:")
        print("   - razao_social")
        print("   - cnae_principal") 
        print("   - natureza_juridica")
        print("   - porte_empresa")
        print("   - situacao_cadastral")
        print("   - data_abertura")
        print("   - etc.")
        
        print(f"\n📝 Primeiros 5 CNPJs do arquivo:")
        for i in range(min(5, len(df_receita))):
            print(f"   {i+1}. {df_receita.iloc[i]['cnpj']}")
    else:
        # Analisar dados disponíveis
        print(f"\n📄 PRIMEIRAS 2 LINHAS:")
        for i in range(min(2, len(df_receita))):
            print(f"\n   LINHA {i+1}:")
            for col in df_receita.columns:
                valor = df_receita.iloc[i][col]
                if pd.notna(valor) and str(valor).strip():
                    print(f"      {col}: {valor}")
    
    print(f"\n💡 RECOMENDAÇÃO:")
    if len(df_receita.columns) == 1:
        print("   📋 Seu arquivo atual só tem CNPJs")
        print("   🔧 Para ter dados completos da Receita Federal, você precisa de:")
        print("      1. Um arquivo com dados completos da Receita")
        print("      2. Ou integração com API da Receita Federal")
        print("      3. Ou consulta manual dos dados")
    else:
        print("   ✅ Arquivo parece ter dados completos!")
        print("   🚀 O script de importação deve funcionar corretamente")

if __name__ == "__main__":
    main()