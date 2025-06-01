#!/usr/bin/env python
"""
🚀 SCRIPT FINAL CORRIGIDO - Importação de Clientes com CNAE Fiscal

✅ CORREÇÕES IMPLEMENTADAS:
- Campo correto 'cnae_fiscal' para CNAE principal
- Campo correto 'cnae_fiscal_descricao' para descrição
- Criação automática de CNAEs secundários
- Decodificação de motivos situação cadastral
- Limpeza de CPF/CNPJ do início dos nomes
- Correção de masters circulares
- Melhor tratamento de dados da Receita Federal

COMO USAR:
1. Coloque na pasta raiz do projeto Django
2. Tenha os arquivos: listare.xlsx, CLIENTEs.xlsx, receita.xlsx
3. Execute: python importar_clientes.py
"""

import os
import sys
import django
import json

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalcomercial.settings')
    django.setup()

import pandas as pd
from datetime import datetime
import re
from django.utils import timezone
from django.db import transaction
from core.models import Cliente, ClienteContato, ClienteCnaeSecundario, Loja, Vendedor

# ✅ NOVO: Dicionário para decodificar motivos da situação cadastral
MOTIVOS_SITUACAO_CADASTRAL = {
    0: "Sem motivo informado",
    1: "Extinção Por Encerramento Liquidação Voluntária",
    18: "Alteração Quadro Societário",
    21: "Incorporação",
    63: "Mudança de Endereço Dentro do Mesmo Município",
    75: "Baixa de Ofício"
}

def converter_para_int(valor):
    """Converte qualquer valor para int, lidando com floats"""
    if pd.isna(valor):
        return None
    try:
        if isinstance(valor, float):
            return int(valor)
        elif isinstance(valor, str):
            if '.' in valor:
                valor = valor.split('.')[0]
            return int(valor)
        else:
            return int(valor)
    except (ValueError, TypeError):
        return None

def converter_codigo_para_string(codigo):
    """Converte código para string, lidando com floats"""
    if pd.isna(codigo):
        return None
    try:
        if isinstance(codigo, float):
            return str(int(codigo))
        elif isinstance(codigo, str):
            if codigo.endswith('.0'):
                return codigo[:-2]
            return codigo.strip()
        else:
            return str(codigo)
    except (ValueError, TypeError):
        return str(codigo) if codigo else None

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

def limpar_nome_cpf_cnpj(nome, cpf_cnpj=None):
    """✨ Remove CPF/CNPJ do início do nome se presente"""
    if pd.isna(nome):
        return nome
    
    nome_str = str(nome).strip()
    
    # Verificar se o nome começa com números (padrão CPF/CNPJ)
    match = re.match(r'^(\d{8,14})\s+(.+)', nome_str)
    if match:
        numero_inicial = match.group(1)
        nome_limpo = match.group(2).strip()
        
        # Se temos o CPF/CNPJ para comparar, verificar se corresponde
        if cpf_cnpj:
            cpf_cnpj_limpo = re.sub(r'\D', '', str(cpf_cnpj))
            if cpf_cnpj_limpo.startswith(numero_inicial):
                return nome_limpo
        else:
            if len(numero_inicial) >= 8:
                return nome_limpo
    
    return nome_str

def determinar_tipo_documento(cpf_cnpj):
    """Determina se é CPF ou CNPJ"""
    if not cpf_cnpj:
        return 'cpf'
    return 'cpf' if len(cpf_cnpj) == 11 else 'cnpj'

def decodificar_motivo_situacao(codigo_motivo):
    """✅ NOVO: Decodifica código do motivo situação cadastral"""
    if pd.isna(codigo_motivo):
        return None
    
    try:
        codigo = int(codigo_motivo)
        return MOTIVOS_SITUACAO_CADASTRAL.get(codigo, f"Motivo código {codigo}")
    except (ValueError, TypeError):
        return str(codigo_motivo)

def processar_cnaes_secundarios(cnaes_string):
    """✅ CORRIGIDO: Processa string de CNAEs secundários com validação robusta"""
    if pd.isna(cnaes_string) or not cnaes_string:
        return []
    
    try:
        # Limpar a string para garantir JSON válido
        cnaes_string = str(cnaes_string).strip()
        
        # Se começar com aspas, remover
        if cnaes_string.startswith('"') and cnaes_string.endswith('"'):
            cnaes_string = cnaes_string[1:-1]
        
        # Trocar aspas simples por duplas para JSON válido
        cnaes_string = cnaes_string.replace("'", '"')
        
        # Parsear JSON
        cnaes_list = json.loads(cnaes_string)
        
        # Processar lista de CNAEs
        cnaes_processados = []
        for i, cnae in enumerate(cnaes_list, 1):
            if isinstance(cnae, dict) and 'codigo' in cnae:
                codigo = str(cnae['codigo']).strip()
                descricao = str(cnae.get('descricao', '')).strip()
                
                # ✅ NOVA VALIDAÇÃO: Verificar se campos são válidos
                if not codigo or codigo == 'nan' or codigo == '':
                    print(f"⚠️  CNAE secundário ignorado: código inválido '{codigo}'")
                    continue
                
                # ✅ NOVA VALIDAÇÃO: Se descrição estiver vazia, pular
                if not descricao or descricao == 'nan' or descricao == '':
                    print(f"⚠️  CNAE secundário ignorado: código {codigo} sem descrição")
                    continue
                
                # ✅ NOVA VALIDAÇÃO: Verificar se código é numérico
                if not codigo.isdigit():
                    print(f"⚠️  CNAE secundário ignorado: código não numérico '{codigo}'")
                    continue
                
                cnaes_processados.append({
                    'codigo': codigo,
                    'descricao': descricao,
                    'ordem': i
                })
        
        return cnaes_processados
        
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        print(f"⚠️  Erro processando CNAEs secundários: {e}")
        return []

def limpar_telefone(telefone):
    """Limpa e formata telefone"""
    if pd.isna(telefone):
        return None
    
    if isinstance(telefone, float):
        tel_str = str(int(telefone))
    else:
        tel_str = str(telefone)
    
    tel_str = re.sub(r'\D', '', tel_str)
    
    if len(tel_str) < 8:
        return None
    
    if len(tel_str) == 8:
        tel_str = '11' + tel_str
    elif len(tel_str) == 9:
        tel_str = '11' + tel_str
    
    return tel_str

def formatar_cep(cep):
    """Formata CEP"""
    if pd.isna(cep):
        return None
    
    if isinstance(cep, float):
        cep_str = str(int(cep)).zfill(8)
    else:
        cep_str = re.sub(r'\D', '', str(cep))
    
    if len(cep_str) == 8:
        return f"{cep_str[:5]}-{cep_str[5:]}"
    
    return cep_str if cep_str else None

def converter_data_timezone_aware(data_valor):
    """Converte data para formato timezone-aware"""
    if pd.isna(data_valor):
        return None
    
    try:
        if hasattr(data_valor, 'date'):
            dt = datetime.combine(data_valor.date(), datetime.min.time())
            return timezone.make_aware(dt, timezone.get_current_timezone())
        elif isinstance(data_valor, str):
            dt = datetime.strptime(data_valor, '%Y-%m-%d')
            return timezone.make_aware(dt, timezone.get_current_timezone())
        elif isinstance(data_valor, datetime):
            return timezone.make_aware(data_valor, timezone.get_current_timezone())
        else:
            dt = datetime.strptime(str(data_valor), '%Y-%m-%d')
            return timezone.make_aware(dt, timezone.get_current_timezone())
    except Exception as e:
        print(f"⚠️  Erro convertendo data timezone-aware {data_valor}: {e}")
        return None

def converter_data_simples(data_valor):
    """Converte data para formato simples (sem timezone)"""
    if pd.isna(data_valor):
        return None
    
    try:
        if hasattr(data_valor, 'date'):
            return data_valor.date()
        elif isinstance(data_valor, str):
            return datetime.strptime(data_valor, '%Y-%m-%d').date()
        return data_valor
    except Exception as e:
        print(f"⚠️  Erro convertendo data simples {data_valor}: {e}")
        return None

def garantir_loja_vendedor(codigo_loja, codigo_vendedor):
    """Cria loja e vendedor se não existirem"""
    
    if codigo_loja and not pd.isna(codigo_loja):
        codigo_loja_int = converter_para_int(codigo_loja)
        if codigo_loja_int:
            codigo_loja_str = str(codigo_loja_int).zfill(3)
            Loja.objects.get_or_create(
                codigo=codigo_loja_str,
                defaults={'nome': f'Loja {codigo_loja_str}', 'ativo': True}
            )
    
    if codigo_vendedor and not pd.isna(codigo_vendedor):
        codigo_vendedor_int = converter_para_int(codigo_vendedor)
        if codigo_vendedor_int:
            codigo_vendedor_str = str(codigo_vendedor_int).zfill(3)
            Vendedor.objects.get_or_create(
                codigo=codigo_vendedor_str,
                defaults={'nome': f'Vendedor {codigo_vendedor_str}', 'ativo': True}
            )

def carregar_dados_receita(arquivo_receita):
    """✅ CORRIGIDO: Carrega dados da Receita Federal com mapeamento correto"""
    if not os.path.exists(arquivo_receita):
        print(f"⚠️  Arquivo {arquivo_receita} não encontrado - pulando dados da Receita")
        return {}
    
    print(f"📖 Carregando dados da Receita Federal...")
    try:
        df_receita = pd.read_excel(arquivo_receita)
        print(f"   📊 {len(df_receita)} registros na Receita Federal")
        
        # Verificar colunas disponíveis
        colunas = list(df_receita.columns)
        print(f"   📋 Principais colunas: {colunas[:10]}...")
        
        # ✅ VERIFICAÇÃO: Campo cnae_fiscal
        if 'cnae_fiscal' in colunas:
            total_cnae = df_receita['cnae_fiscal'].notna().sum()
            print(f"   🎯 Campo 'cnae_fiscal' encontrado: {total_cnae} registros com CNAE")
        else:
            print(f"   ⚠️  Campo 'cnae_fiscal' NÃO encontrado! Colunas disponíveis: {colunas}")
        
        # ✅ VERIFICAÇÃO: CNAEs secundários
        if 'cnaes_secundarios' in colunas:
            total_cnaes_sec = df_receita['cnaes_secundarios'].notna().sum()
            print(f"   📋 Campo 'cnaes_secundarios' encontrado: {total_cnaes_sec} registros com CNAEs secundários")
        
        # Indexar por CPF/CNPJ
        receita_dict = {}
        for index, row in df_receita.iterrows():
            cpf_cnpj_limpo = limpar_cpf_cnpj(row.get('cnpj'))
            if cpf_cnpj_limpo:
                receita_dict[cpf_cnpj_limpo] = row.to_dict()
        
        print(f"   📊 {len(receita_dict)} registros indexados por CPF/CNPJ")
        return receita_dict
        
    except Exception as e:
        print(f"❌ Erro carregando receita.xlsx: {e}")
        return {}

def main():
    """Função principal de importação"""
    
    print("🚀 IMPORTAÇÃO CORRIGIDA COM CNAE FISCAL - Iniciando...")
    print("🗑️  ZERANDO A BASE DE DADOS...")
    
    # Zerar base de dados
    with transaction.atomic():
        ClienteCnaeSecundario.objects.all().delete()
        ClienteContato.objects.all().delete()
        Cliente.objects.all().delete()
        print("   ✅ Base zerada com sucesso!")
    
    # Verificar arquivos
    arquivos_necessarios = ['listare.xlsx', 'CLIENTEs.xlsx']
    for arquivo in arquivos_necessarios:
        if not os.path.exists(arquivo):
            print(f"❌ Arquivo {arquivo} não encontrado!")
            return
    
    # Carregar dados da Receita Federal
    dados_receita = carregar_dados_receita('receita.xlsx')
    
    # Carregar dados principais
    print("📖 Carregando LISTARE...")
    df_listare = pd.read_excel('listare.xlsx')
    print(f"   📊 {len(df_listare)} registros no LISTARE")
    
    print("📖 Carregando CLIENTEs (dados mais atualizados)...")
    df_cliente = pd.read_excel('CLIENTEs.xlsx')
    print(f"   📊 {len(df_cliente)} registros no CLIENTEs")
    
    # Contadores
    criados = 0
    erros = 0
    cnaes_secundarios_criados = 0
    erros_detalhados = []
    
    print("\n🔄 Processando registros...")
    
    for index, row in df_listare.iterrows():
        try:
            # Dados do LISTARE
            codigo_raw = row['CODIGO'] if 'CODIGO' in row else row.get('codcli')
            codigo = converter_codigo_para_string(codigo_raw)
            
            if not codigo:
                erro = f"Linha {index}: código inválido '{codigo_raw}'"
                erros_detalhados.append(erro)
                erros += 1
                continue
            
            # ✅ CORREÇÃO: Detectar e corrigir masters circulares
            codigo_master = converter_codigo_para_string(row.get('COD.MASTER'))
            if codigo_master == codigo:
                codigo_master = None  # Evitar master circular
            
            cpf_cnpj = limpar_cpf_cnpj(row['cnpj'])
            nome = str(row['NOME']).strip() if pd.notna(row['NOME']) else 'Cliente'
            # ✅ LIMPEZA: Remover CPF/CNPJ do início do nome
            nome = limpar_nome_cpf_cnpj(nome, cpf_cnpj)
            
            situacao = str(row['RECEITA']).strip() if pd.notna(row['RECEITA']) else 'ATIVA'
            cod_vendedor = row['VEND'] if pd.notna(row['VEND']) else None
            cod_loja = row['LOJA'] if pd.notna(row['LOJA']) else None
            
            # Buscar dados complementares no CLIENTEs
            codigo_int = converter_para_int(codigo)
            cliente_extra = pd.DataFrame()
            
            if codigo_int:
                for col_name in ['CODCLI', 'codcli', 'codigo', 'CODIGO']:
                    if col_name in df_cliente.columns:
                        cliente_extra = df_cliente[df_cliente[col_name] == codigo_int]
                        if not cliente_extra.empty:
                            break
            
            # Garantir loja e vendedor
            garantir_loja_vendedor(cod_loja, cod_vendedor)
            
            # Dados básicos do cliente
            dados = {
                'codigo': codigo,
                'codigo_master': codigo_master,
                'cpf_cnpj': cpf_cnpj,
                'tipo_documento': determinar_tipo_documento(cpf_cnpj),
                'nome': nome,
                'situacao_cadastral': situacao,
                # ✅ ATIVO baseado na situação
                'ativo': situacao.upper() in ['ATIVA', 'ATIVO', 'REGULAR'],
                'data_cadastro': timezone.now()
            }
            
            # Adicionar códigos de loja e vendedor
            if cod_loja and not pd.isna(cod_loja):
                codigo_loja_int = converter_para_int(cod_loja)
                if codigo_loja_int:
                    dados['codigo_loja'] = str(codigo_loja_int).zfill(3)
            
            if cod_vendedor and not pd.isna(cod_vendedor):
                codigo_vendedor_int = converter_para_int(cod_vendedor)
                if codigo_vendedor_int:
                    dados['codigo_vendedor'] = str(codigo_vendedor_int).zfill(3)
            
            # Adicionar dados básicos do LISTARE
            if pd.notna(row.get('CEP')):
                dados['cep'] = formatar_cep(row['CEP'])
            
            # ✅ PRIORIZAR dados do CLIENTEs.xlsx (MAIS ATUALIZADOS)
            if not cliente_extra.empty:
                extra = cliente_extra.iloc[0]
                
                # SEMPRE usar nome do CLIENTEs se disponível
                nome_cliente = str(extra.get('NOM', extra.get('nome', ''))).strip() if pd.notna(extra.get('NOM', extra.get('nome'))) else None
                if nome_cliente and nome_cliente != 'nan':
                    nome_cliente = limpar_nome_cpf_cnpj(nome_cliente, cpf_cnpj)
                    dados['nome'] = nome_cliente
                
                # ✅ USAR CAD e ULTMOV conforme solicitado
                data_cad = converter_data_timezone_aware(extra.get('CAD'))
                if data_cad:
                    dados['data_cadastro'] = data_cad
                
                data_ultmov = converter_data_simples(extra.get('ULTMOV'))
                if data_ultmov:
                    dados['data_ultima_compra'] = data_ultmov
                
                # Outros dados do CLIENTEs
                campos_mapeamento = {
                    'nome_fantasia': ['FANT', 'nome_fantasia'],
                    'bairro': ['BAI', 'bairro'],
                    'cidade': ['CID', 'cidade'],
                    'estado': ['UF', 'estado', 'uf'],
                    'inscricao_estadual': ['IE', 'inscricao_estadual'],
                    'inscricao_municipal': ['IM', 'inscricao_municipal'],
                    'email': ['EMAIL', 'email'],
                    'observacoes': ['CONTATO', 'observacoes', 'contato'],
                }
                
                for campo_destino, possiveis_campos in campos_mapeamento.items():
                    for campo_origem in possiveis_campos:
                        if campo_origem in extra and pd.notna(extra[campo_origem]):
                            valor = str(extra[campo_origem]).strip()
                            if valor and valor != 'nan':
                                dados[campo_destino] = valor
                                break
                
                # Endereço composto
                endereco_partes = []
                for campo in ['END1', 'END2', 'END3', 'END4', 'endereco']:
                    if campo in extra and pd.notna(extra[campo]):
                        parte = str(extra[campo]).strip()
                        if parte and parte != 'nan':
                            endereco_partes.append(parte)
                if endereco_partes:
                    dados['endereco'] = ' '.join(endereco_partes)
                
                # CEP (priorizar CLIENTEs)
                for campo_cep in ['CEP', 'cep']:
                    if campo_cep in extra and pd.notna(extra[campo_cep]):
                        dados['cep'] = formatar_cep(extra[campo_cep])
                        break
                
                # Telefone
                for campo_tel in ['FONE1', 'telefone', 'FONE']:
                    if campo_tel in extra and pd.notna(extra[campo_tel]):
                        dados['telefone'] = limpar_telefone(extra[campo_tel])
                        break
            
            # ✅ ADICIONAR DADOS DA RECEITA FEDERAL (MAPEAMENTO CORRIGIDO)
            cnaes_secundarios_para_criar = []
            
            if cpf_cnpj and cpf_cnpj in dados_receita:
                receita = dados_receita[cpf_cnpj]
                
                # ✅ MAPEAMENTO CORRIGIDO - CNAE_FISCAL é o campo correto!
                mapeamento_receita = {
                    'nome_razao_social': ['razao_social', 'nome_empresarial', 'nome'],
                    'natureza_juridica': ['natureza_juridica'],
                    'codigo_natureza_juridica': ['codigo_natureza_juridica'],
                    'porte_empresa': ['porte', 'porte_empresa'],
                    # ✅ CORREÇÃO PRINCIPAL: cnae_fiscal é o campo correto
                    'cnae_principal': ['cnae_fiscal', 'cnae_principal', 'cnae'],
                    'cnae_descricao': ['cnae_fiscal_descricao', 'descricao_cnae', 'cnae_descricao'],
                    'capital_social': ['capital_social'],
                    'opcao_pelo_simples': ['opcao_pelo_simples', 'simples_nacional'],
                    'opcao_pelo_mei': ['opcao_pelo_mei', 'mei'],
                    'data_abertura': ['data_inicio_atividade', 'data_abertura'],
                    'data_inicio_atividade': ['data_inicio_atividade'],
                    # ✅ SITUAÇÃO DA RECEITA FEDERAL
                    'situacao_cadastral': ['situacao_cadastral', 'descricao_situacao_cadastral'],
                    'data_situacao_cadastral': ['data_situacao_cadastral'],
                    # ✅ NOVO: Motivo com decodificação
                    'motivo_situacao_cadastral': ['motivo_situacao_cadastral', 'descricao_motivo_situacao_cadastral'],
                    # Endereço
                    'endereco': ['logradouro'],
                    'numero': ['numero'],
                    'complemento': ['complemento'],
                    'bairro': ['bairro'],
                    'cidade': ['municipio', 'cidade'],
                    'estado': ['uf', 'estado'],
                    'cep': ['cep'],
                    # Contatos
                    'telefone': ['ddd_telefone_1'],
                }
                
                for campo_destino, possiveis_campos in mapeamento_receita.items():
                    for campo_origem in possiveis_campos:
                        if campo_origem in receita and pd.notna(receita[campo_origem]):
                            valor = receita[campo_origem]
                            
                            # Conversões específicas CORRIGIDAS
                            if campo_destino in ['data_abertura', 'data_inicio_atividade', 'data_situacao_cadastral']:
                                valor = converter_data_simples(valor)
                            elif campo_destino == 'motivo_situacao_cadastral':
                                # ✅ NOVO: Decodificar motivo
                                valor = decodificar_motivo_situacao(valor)
                            elif campo_destino in ['opcao_pelo_simples', 'opcao_pelo_mei']:
                                if isinstance(valor, bool):
                                    valor = valor
                                elif isinstance(valor, str):
                                    valor = valor.lower() in ['true', 'sim', 's', '1', 'ativo', 'optante']
                                else:
                                    valor = bool(valor) if valor else False
                            elif campo_destino == 'capital_social':
                                try:
                                    valor = float(valor) if valor else None
                                except:
                                    valor = None
                            elif campo_destino == 'codigo_natureza_juridica':
                                valor = str(valor).strip() if valor else None
                            elif isinstance(valor, str):
                                valor = valor.strip()
                                if valor.lower() in ['nan', '', 'null']:
                                    valor = None
                            
                            if valor is not None and valor != '':
                                dados[campo_destino] = valor
                                break
                
                # ✅ NOVO: Processar CNAEs secundários
                if 'cnaes_secundarios' in receita and pd.notna(receita['cnaes_secundarios']):
                    cnaes_secundarios_para_criar = processar_cnaes_secundarios(receita['cnaes_secundarios'])
            
            # ✅ Criar cliente
            try:
                cliente = Cliente.objects.create(**dados)
                criados += 1


                # ✅ NOVO: Criar CNAEs secundários com validação robusta
                for cnae_info in cnaes_secundarios_para_criar:
                    try:
                        # ✅ VALIDAÇÃO EXTRA: Verificar se os dados são válidos antes de criar
                        codigo_cnae = cnae_info.get('codigo', '').strip()
                        descricao_cnae = cnae_info.get('descricao', '').strip()
                        ordem = cnae_info.get('ordem', 1)
                        
                        # Validações antes de criar
                        if not codigo_cnae or len(codigo_cnae) < 7:
                            print(f"⚠️  CNAE secundário ignorado para cliente {codigo}: código inválido '{codigo_cnae}'")
                            continue
                        
                        if not descricao_cnae or len(descricao_cnae) < 5:
                            print(f"⚠️  CNAE secundário ignorado para cliente {codigo}: descrição inválida '{descricao_cnae}'")
                            continue
                        
                        # Verificar se já existe para evitar duplicatas
                        existe = ClienteCnaeSecundario.objects.filter(
                            cliente=cliente,
                            codigo_cnae=codigo_cnae
                        ).exists()
                        
                        if existe:
                            print(f"⚠️  CNAE secundário já existe para cliente {codigo}: {codigo_cnae}")
                            continue
                        
                        # Criar o CNAE secundário
                        ClienteCnaeSecundario.objects.create(
                            cliente=cliente,
                            codigo_cnae=codigo_cnae,
                            descricao_cnae=descricao_cnae,
                            ordem=ordem
                        )
                        cnaes_secundarios_criados += 1
                        
                    except Exception as cnae_error:
                        print(f"⚠️  Erro criando CNAE secundário para cliente {codigo}: {cnae_error}")
                        # Continuar processamento mesmo com erro

                
            except Exception as create_error:
                if "duplicate key value" in str(create_error):
                    erro = f"Linha {index}, Código {codigo}: Cliente duplicado"
                else:
                    erro = f"Linha {index}, Código {codigo}: {str(create_error)}"
                erros_detalhados.append(erro)
                erros += 1
                continue
            
            if criados % 100 == 0:
                print(f"   📊 Processados: {criados} clientes, {cnaes_secundarios_criados} CNAEs secundários")
            
        except Exception as e:
            erro = f"Linha {index}, Código {codigo_raw}: {str(e)}"
            erros_detalhados.append(erro)
            erros += 1
            continue
    
    # Relatório final
    print(f"\n🎉 IMPORTAÇÃO CONCLUÍDA!")
    print(f"✅ Clientes criados: {criados}")
    print(f"✅ CNAEs secundários criados: {cnaes_secundarios_criados}")
    print(f"❌ Erros: {erros}")
    print(f"📊 Total processado: {len(df_listare)}")
    
    # ✅ NOVO: Estatísticas detalhadas dos dados da Receita Federal
    clientes_com_cnae = Cliente.objects.filter(cnae_principal__isnull=False).exclude(cnae_principal='').count()
    clientes_com_receita = Cliente.objects.filter(natureza_juridica__isnull=False).exclude(natureza_juridica='').count()
    clientes_com_situacao_receita = Cliente.objects.filter(situacao_cadastral__isnull=False).exclude(situacao_cadastral='').count()
    total_cnaes_secundarios = ClienteCnaeSecundario.objects.count()
    
    print(f"\n📊 ESTATÍSTICAS DA RECEITA FEDERAL:")
    print(f"   🎯 Clientes com CNAE Principal: {clientes_com_cnae}")
    print(f"   🏢 Clientes com dados da Receita: {clientes_com_receita}")
    print(f"   📋 Clientes com situação cadastral: {clientes_com_situacao_receita}")
    print(f"   📝 Total de CNAEs secundários: {total_cnaes_secundarios}")
    
    # ✅ NOVO: Verificação de qualidade dos dados CNAE
    if clientes_com_cnae > 0:
        print(f"   ✅ SUCESSO: Campo CNAE Principal foi corrigido!")
        
        # Mostrar alguns exemplos
        exemplos_cnae = Cliente.objects.filter(
            cnae_principal__isnull=False
        ).exclude(cnae_principal='').values_list(
            'codigo', 'nome', 'cnae_principal', 'cnae_descricao'
        )[:3]
        
        print(f"\n🔍 EXEMPLOS DE CNAEs IMPORTADOS:")
        for codigo, nome, cnae_principal, cnae_descricao in exemplos_cnae:
            print(f"   • Cliente {codigo} ({nome[:30]}...)")
            print(f"     CNAE: {cnae_principal} - {cnae_descricao[:50]}...")
    else:
        print(f"   ❌ PROBLEMA: CNAE Principal ainda não está sendo importado!")
    
    if erros_detalhados:
        print(f"\n❌ DETALHES DOS ERROS ({len(erros_detalhados)}):")
        for i, erro in enumerate(erros_detalhados[:10], 1):  # Mostrar até 10 erros
            print(f"   {i}. {erro}")
        
        if len(erros_detalhados) > 10:
            print(f"   ... e mais {len(erros_detalhados) - 10} erros")
    
    # ✅ NOVO: Verificação final e sugestões
    print(f"\n🔧 PRÓXIMOS PASSOS RECOMENDADOS:")
    print(f"   1. Verificar se CNAEs principais estão preenchidos")
    print(f"   2. Confirmar criação de CNAEs secundários no admin")
    print(f"   3. Testar busca de clientes por CNAE")
    print(f"   4. Validar dados da Receita Federal importados")
    
    if clientes_com_cnae == 0:
        print(f"\n⚠️  ATENÇÃO: Se CNAE Principal não foi importado:")
        print(f"   - Verifique se o arquivo receita.xlsx tem o campo 'cnae_fiscal'")
        print(f"   - Confirme se os CPF/CNPJs coincidem entre os arquivos")
        print(f"   - Execute novamente após corrigir os problemas")

if __name__ == "__main__":
    main()