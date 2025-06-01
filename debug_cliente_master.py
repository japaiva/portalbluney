#!/usr/bin/env python
"""
Script para debug do cliente master 88641
"""

import os
import sys
import django

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalcomercial.settings')
    django.setup()

from core.models import Cliente
from django.db.models import Q

def main():
    print("🔍 DEBUG - Cliente Master 88641...")
    
    # 1. Verificar se o cliente master existe
    print("\n1️⃣ VERIFICAÇÃO DO CLIENTE MASTER 88641:")
    cliente_master = Cliente.objects.filter(codigo='88641').first()
    
    if cliente_master:
        print(f"✅ ENCONTRADO: {cliente_master.codigo} - {cliente_master.nome}")
        print(f"   Ativo: {cliente_master.ativo}")
        print(f"   Código Master: {cliente_master.codigo_master}")
        print(f"   É cliente principal? {cliente_master.is_cliente_principal()}")
        print(f"   CPF/CNPJ: {cliente_master.cpf_cnpj}")
        print(f"   Cidade: {cliente_master.cidade}")
    else:
        print("❌ Cliente master 88641 NÃO ENCONTRADO!")
        
        # Buscar códigos próximos
        print("\n🔍 Buscando códigos próximos:")
        for codigo in ['88640', '88641', '88642', '88643']:
            cliente = Cliente.objects.filter(codigo=codigo).first()
            if cliente:
                print(f"   ✅ {codigo}: {cliente.nome} (Master: {cliente.codigo_master})")
            else:
                print(f"   ❌ {codigo}: NÃO ENCONTRADO")
        return
    
    # 2. Verificar por que não aparece na busca da view
    print("\n2️⃣ TESTE DA BUSCA DA VIEW (cliente_list):")
    
    # Simular exatamente o que a view faz
    print("   🔸 Filtro da view (apenas clientes principais):")
    clientes_principais = Cliente.objects.filter(
        Q(codigo_master__isnull=True) | Q(codigo_master='')
    )
    
    cliente_na_busca = clientes_principais.filter(codigo='88641').first()
    if cliente_na_busca:
        print(f"      ✅ Cliente 88641 APARECE no filtro de clientes principais")
    else:
        print(f"      ❌ Cliente 88641 NÃO APARECE no filtro de clientes principais")
        print(f"         Motivo: codigo_master = '{cliente_master.codigo_master}'")
    
    # 3. Teste de busca por termo
    print("\n   🔸 Teste de busca por diferentes termos:")
    termos = ['88641', 'EMANUEL', 'emanuel', 'CORREIA', 'correia']
    
    for termo in termos:
        print(f"      🔍 Buscando '{termo}':")
        
        # Busca completa (incluindo sub-clientes)
        resultados_completos = Cliente.objects.filter(
            Q(nome__icontains=termo) | 
            Q(codigo__icontains=termo) |
            Q(cpf_cnpj__icontains=termo)
        )
        
        # Busca apenas clientes principais (como na view)
        resultados_principais = Cliente.objects.filter(
            Q(codigo_master__isnull=True) | Q(codigo_master='')
        ).filter(
            Q(nome__icontains=termo) | 
            Q(codigo__icontains=termo) |
            Q(cpf_cnpj__icontains=termo)
        )
        
        print(f"         Total encontrados: {resultados_completos.count()}")
        print(f"         Apenas principais: {resultados_principais.count()}")
        
        if resultados_completos.count() > 0:
            for cliente in resultados_completos[:3]:
                principal = "✅ Principal" if cliente.is_cliente_principal() else f"🔗 Sub-cliente de {cliente.codigo_master}"
                print(f"           {cliente.codigo} - {cliente.nome} ({principal})")
    
    # 4. Verificar sub-clientes do master
    print(f"\n3️⃣ SUB-CLIENTES DO MASTER {cliente_master.codigo}:")
    sub_clientes = cliente_master.get_sub_clientes()
    if sub_clientes.exists():
        print(f"   📊 Total de sub-clientes: {sub_clientes.count()}")
        for sub in sub_clientes:
            print(f"      🔗 {sub.codigo} - {sub.nome}")
    else:
        print("   📭 Nenhum sub-cliente encontrado")
    
    # 5. Verificar todos os clientes com código_master preenchido
    print("\n4️⃣ ANÁLISE GERAL DOS CÓDIGOS MASTER:")
    clientes_com_master = Cliente.objects.exclude(
        Q(codigo_master__isnull=True) | Q(codigo_master='')
    )
    print(f"   📊 Total de sub-clientes no sistema: {clientes_com_master.count()}")
    
    masters_unicos = clientes_com_master.values_list('codigo_master', flat=True).distinct()
    print(f"   📊 Códigos master únicos: {len(masters_unicos)}")
    
    print("\n   🔍 Verificando se os masters existem:")
    masters_inexistentes = []
    for master_code in masters_unicos:
        if not Cliente.objects.filter(codigo=master_code).exists():
            masters_inexistentes.append(master_code)
    
    if masters_inexistentes:
        print(f"   ⚠️  PROBLEMA: {len(masters_inexistentes)} códigos master NÃO existem como clientes:")
        for code in masters_inexistentes[:10]:  # Mostrar apenas os primeiros 10
            sub_clientes_orfaos = Cliente.objects.filter(codigo_master=code)
            print(f"      ❌ Master {code} (tem {sub_clientes_orfaos.count()} sub-cliente(s) órfãos)")
    else:
        print("   ✅ Todos os códigos master têm clientes correspondentes")
    
    # 6. Recomendações
    print("\n5️⃣ RECOMENDAÇÕES:")
    
    if cliente_master.codigo_master:
        print("   🚨 PROBLEMA IDENTIFICADO:")
        print(f"      O cliente {cliente_master.codigo} tem codigo_master = '{cliente_master.codigo_master}'")
        print("      Isso significa que ele É um sub-cliente, não um master!")
        print("      Por isso não aparece na busca de clientes principais.")
        
        print("\n   💡 SOLUÇÕES:")
        print("      1. Tornar o cliente 88641 um cliente principal:")
        print("         - Limpar o campo codigo_master")
        print("      2. Buscar o verdadeiro cliente master")
        print("      3. Ajustar a interface para mostrar sub-clientes na busca")
        
        # Oferecer correção
        resposta = input("\nDeseja tornar o cliente 88641 um cliente principal? (s/n): ")
        if resposta.lower() == 's':
            cliente_master.codigo_master = None
            cliente_master.save()
            print("✅ Cliente 88641 agora é um cliente principal!")
    else:
        print("   ✅ Cliente master está correto")
        print("   💡 Verifique se a busca na interface está funcionando corretamente")

if __name__ == "__main__":
    main()