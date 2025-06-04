
# SCRIPT DE RESTAURAÇÃO
# Execute no Django shell para restaurar o backup

import json
from django.core import serializers
from io import StringIO

def restaurar_backup():
    """Restaura o backup criado em backup_20250602_140508"""
    
    print("ATENÇÃO: Isso vai SOBRESCREVER os dados atuais!")
    confirmacao = input("Digite 'CONFIRMAR' para continuar: ")
    
    if confirmacao != "CONFIRMAR":
        print("Restauração cancelada")
        return
    
    # Restaurar Clientes
    print("Restaurando clientes...")
    with open("backup_20250602_140508/clientes_backup.json", 'r', encoding='utf-8') as f:
        clientes_data = f.read()
    
    # Limpar tabela atual
    from core.models import Cliente
    Cliente.objects.all().delete()
    
    # Carregar backup
    for obj in serializers.deserialize('json', clientes_data):
        obj.save()
    
    print("✅ Clientes restaurados")
    
    # Restaurar Vendas
    print("Restaurando vendas...")
    with open("backup_20250602_140508/vendas_backup.json", 'r', encoding='utf-8') as f:
        vendas_data = f.read()
    
    from core.models import Vendas
    Vendas.objects.all().delete()
    
    for obj in serializers.deserialize('json', vendas_data):
        obj.save()
    
    print("✅ Vendas restauradas")
    
    # Restaurar Contatos
    print("Restaurando contatos...")
    with open("backup_20250602_140508/contatos_backup.json", 'r', encoding='utf-8') as f:
        contatos_data = f.read()
    
    from core.models import ClienteContato
    ClienteContato.objects.all().delete()
    
    for obj in serializers.deserialize('json', contatos_data):
        obj.save()
    
    print("✅ Contatos restaurados")
    print("BACKUP RESTAURADO COM SUCESSO!")

# Para executar: restaurar_backup()
