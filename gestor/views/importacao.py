# gestor/views/importacao.py - Função atualizada

import logging
import pandas as pd
from decimal import Decimal
from datetime import datetime, date
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q

from core.models import (Cliente, Produto, GrupoProduto, Fabricante, 
                        Loja, Vendedor, Vendas)
from core.forms import ImportarVendasForm

logger = logging.getLogger(__name__)

@login_required
def importar_vendas(request):
    """Importação BI com filtros de data e opções de limpeza"""
    if request.method == 'POST':
        form = ImportarVendasForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # ===== EXTRAIR DADOS DO FORMULÁRIO =====
                data_inicio = form.cleaned_data.get('data_inicio')
                data_fim = form.cleaned_data.get('data_fim')
                limpar_periodo = form.cleaned_data.get('limpar_registros_periodo', False)
                limpar_toda_base = form.cleaned_data.get('limpar_toda_base', False)
                
                # ===== CARREGAR ARQUIVO PRINCIPAL =====
                arquivo_bi = request.FILES['arquivo_csv']
                nome_arquivo = arquivo_bi.name.lower()
                
                # Ler planilha BI
                if nome_arquivo.endswith('.xlsx'):
                    df_bi = pd.read_excel(arquivo_bi, sheet_name=0, engine='openpyxl', dtype=str)
                elif nome_arquivo.endswith('.csv'):
                    df_bi = pd.read_csv(arquivo_bi, encoding='utf-8', sep=',', dtype=str)
                else:
                    messages.error(request, "❌ Formato de arquivo não suportado. Use CSV ou Excel (.xlsx)")
                    return redirect('gestor:importar_vendas')

                messages.info(request, f"📊 Arquivo BI carregado: {len(df_bi)} registros encontrados")
                
                # ===== CARREGAR PLANILHAS AUXILIARES =====
                planilhas_aux = {}
                
                # Tentar carregar planilhas auxiliares enviadas via formulário
                for campo, nome_planilha in [
                    ('arquivo_produtos', 'produtos'),
                    ('arquivo_classes', 'classes'), 
                    ('arquivo_fabricantes', 'fabricantes')
                ]:
                    if campo in request.FILES:
                        try:
                            arquivo_aux = request.FILES[campo]
                            df_aux = pd.read_excel(arquivo_aux, sheet_name=0, dtype=str)
                            df_aux.columns = df_aux.columns.str.strip().str.upper()
                            planilhas_aux[nome_planilha] = df_aux
                            messages.success(request, f"✅ Planilha {nome_planilha.upper()} carregada: {len(df_aux)} registros")
                        except Exception as e:
                            messages.warning(request, f"⚠️ Erro ao carregar {nome_planilha}: {str(e)}")
                
                # Se arquivo principal for Excel com múltiplas planilhas, tentar carregar auxiliares automaticamente
                if nome_arquivo.endswith('.xlsx') and len(planilhas_aux) == 0:
                    try:
                        xls_file = pd.ExcelFile(arquivo_bi)
                        messages.info(request, f"🔍 Buscando planilhas auxiliares no arquivo: {xls_file.sheet_names}")
                        
                        for sheet_name in xls_file.sheet_names:
                            sheet_upper = sheet_name.upper().strip()
                            
                            if sheet_upper in ['CLASSE', 'CLASSES'] or 'CLASS' in sheet_upper:
                                planilhas_aux['classes'] = pd.read_excel(xls_file, sheet_name=sheet_name, dtype=str)
                                planilhas_aux['classes'].columns = planilhas_aux['classes'].columns.str.strip().str.upper()
                                messages.success(request, f"✅ CLASSE encontrada: {len(planilhas_aux['classes'])} registros")
                            elif sheet_upper in ['PRODUTOS', 'PRODUTO'] or 'PRODUTO' in sheet_upper:
                                planilhas_aux['produtos'] = pd.read_excel(xls_file, sheet_name=sheet_name, dtype=str)
                                planilhas_aux['produtos'].columns = planilhas_aux['produtos'].columns.str.strip().str.upper()
                                messages.success(request, f"✅ PRODUTOS encontrada: {len(planilhas_aux['produtos'])} registros")
                            elif sheet_upper in ['FABR', 'FABRICANTES'] or 'FABRIC' in sheet_upper:
                                planilhas_aux['fabricantes'] = pd.read_excel(xls_file, sheet_name=sheet_name, dtype=str)
                                planilhas_aux['fabricantes'].columns = planilhas_aux['fabricantes'].columns.str.strip().str.upper()
                                messages.success(request, f"✅ FABRICANTES encontrada: {len(planilhas_aux['fabricantes'])} registros")
                        
                    except Exception as e:
                        messages.warning(request, f"⚠️ Erro ao buscar planilhas auxiliares: {str(e)}")
                
                # ===== NORMALIZAR COLUNAS =====
                df_bi.columns = df_bi.columns.str.strip().str.upper()
                messages.info(request, f"🔍 Colunas do BI: {list(df_bi.columns)}")
                
                # ===== FILTRAR DADOS POR DATA (SE INFORMADO) =====
                df_processamento = df_bi.copy()
                
                if data_inicio or data_fim:
                    # Verificar se existe coluna de data no arquivo
                    colunas_data_possiveis = ['DATA', 'DATA_VENDA', 'DT_VENDA', 'ANOMES']
                    coluna_data_encontrada = None
                    
                    for col in colunas_data_possiveis:
                        if col in df_processamento.columns:
                            coluna_data_encontrada = col
                            break
                    
                    if coluna_data_encontrada:
                        try:
                            # Converter coluna para datetime
                            if coluna_data_encontrada == 'ANOMES':
                                # Formato ANOMES (ex: 2412 = dezembro/2024)
                                df_processamento['data_convertida'] = pd.to_datetime(
                                    '20' + df_processamento[coluna_data_encontrada].str[:2] + '-' + 
                                    df_processamento[coluna_data_encontrada].str[2:] + '-01',
                                    format='%Y-%m-%d'
                                ).dt.date
                            else:
                                df_processamento['data_convertida'] = pd.to_datetime(
                                    df_processamento[coluna_data_encontrada]
                                ).dt.date
                            
                            # Aplicar filtros de data
                            if data_inicio:
                                df_processamento = df_processamento[
                                    df_processamento['data_convertida'] >= data_inicio
                                ]
                            
                            if data_fim:
                                df_processamento = df_processamento[
                                    df_processamento['data_convertida'] <= data_fim
                                ]
                            
                            messages.info(request, 
                                f"📅 Filtro de data aplicado: {len(df_processamento)} registros restantes "
                                f"(de {len(df_bi)} originais)"
                            )
                            
                        except Exception as e:
                            messages.warning(request, f"⚠️ Erro ao filtrar por data: {str(e)}")
                    else:
                        messages.warning(request, 
                            "⚠️ Coluna de data não encontrada. Filtro de data ignorado. "
                            f"Colunas disponíveis: {list(df_bi.columns)}"
                        )
                
                # ===== LIMPEZA DA BASE ANTERIOR =====
                if limpar_toda_base:
                    count_deletados = Vendas.objects.all().count()
                    Vendas.objects.all().delete()
                    messages.warning(request, f"🗑️ TODA a base de vendas foi zerada: {count_deletados} registros removidos")
                    
                elif limpar_periodo and (data_inicio or data_fim):
                    # Construir filtro para o período
                    filtro_periodo = Q()
                    
                    if data_inicio:
                        filtro_periodo &= Q(data_venda__gte=data_inicio)
                    
                    if data_fim:
                        filtro_periodo &= Q(data_venda__lte=data_fim)
                    
                    vendas_periodo = Vendas.objects.filter(filtro_periodo)
                    count_periodo = vendas_periodo.count()
                    
                    if count_periodo > 0:
                        vendas_periodo.delete()
                        period_str = ""
                        if data_inicio and data_fim:
                            period_str = f"entre {data_inicio.strftime('%d/%m/%Y')} e {data_fim.strftime('%d/%m/%Y')}"
                        elif data_inicio:
                            period_str = f"a partir de {data_inicio.strftime('%d/%m/%Y')}"
                        elif data_fim:
                            period_str = f"até {data_fim.strftime('%d/%m/%Y')}"
                        
                        messages.info(request, f"🗑️ Registros do período removidos: {count_periodo} vendas {period_str}")
                    else:
                        messages.info(request, "ℹ️ Nenhum registro encontrado no período especificado para remoção")
                
                # ===== PROCESSAMENTO =====
                total_registros = len(df_processamento)
                messages.info(request, f"🔄 Iniciando processamento de {total_registros} registros...")
                
                # Contadores
                vendas_criadas = 0
                clientes_criados = 0
                produtos_criados = 0
                grupos_criados = 0
                fabricantes_criados = 0
                vendedores_criados = 0
                lojas_criadas = 0
                erros = []
                
                # ===== PROCESSAR REGISTROS =====
                total_linhas = len(df_processamento)
                for index, row in df_processamento.iterrows():
                    try:
                        # Mostrar progresso a cada 100 registros
                        if (index + 1) % 100 == 0:
                            messages.info(request, f"📊 Processando... {index + 1}/{total_linhas} registros")
                        
                        with transaction.atomic():
                            # Extrair dados básicos
                            cnpj_cpf = str(row['CNPJ']).strip() if pd.notna(row['CNPJ']) else ''
                            codigo_produto_bi = str(row['CODPRO']).strip() if pd.notna(row['CODPRO']) else ''
                            codigo_loja = str(row['NUMLOJ']).strip()
                            codigo_vendedor = str(row['CODVEN']).strip() if pd.notna(row['CODVEN']) else '001'
                            
                            # === CRIAR/BUSCAR CLIENTE ===
                            cliente = None
                            if cnpj_cpf:
                                cnpj_cpf_limpo = ''.join(filter(str.isdigit, cnpj_cpf))
                                cliente = Cliente.objects.filter(cpf_cnpj__icontains=cnpj_cpf_limpo).first()
                                
                                if not cliente:
                                    codigo_cliente = cnpj_cpf_limpo[:10] if len(cnpj_cpf_limpo) >= 10 else cnpj_cpf_limpo.ljust(10, '0')
                                    nome_cliente = str(row['CLIENTE']).strip()
                                    
                                    cliente = Cliente.objects.create(
                                        codigo=codigo_cliente,
                                        nome=nome_cliente[:100],
                                        status='rascunho',
                                        cpf_cnpj=cnpj_cpf_limpo,
                                        tipo_documento='cnpj' if len(cnpj_cpf_limpo) == 14 else 'cpf',
                                        codigo_loja=codigo_loja,
                                        codigo_vendedor=codigo_vendedor,
                                        uf=str(row.get('UF', 'SP')).strip()
                                    )
                                    clientes_criados += 1
                            
                            if not cliente:
                                erros.append(f"Linha {index + 2}: Cliente não encontrado/criado")
                                continue
                            
                            # === CRIAR/BUSCAR PRODUTO COM PLANILHAS AUXILIARES ===
                            produto = None
                            grupo = None
                            fabricante = None
                            
                            if codigo_produto_bi:
                                codigo_produto_formatado = codigo_produto_bi.zfill(6)
                                produto = Produto.objects.filter(codigo=codigo_produto_formatado).first()
                                
                                if produto:
                                    grupo = produto.grupo
                                    fabricante = produto.fabricante
                                else:
                                    # Valores padrão
                                    codigo_grupo = '0001'
                                    codigo_fabricante = '001'
                                    desc_produto = str(row['PRODUTO']).strip()
                                    desc_grupo = 'GRUPO PADRÃO'
                                    desc_fabricante = 'FABRICANTE PADRÃO'
                                    
                                    # Buscar nas planilhas auxiliares
                                    if 'produtos' in planilhas_aux:
                                        df_produtos = planilhas_aux['produtos']
                                        produto_planilha = df_produtos[
                                            df_produtos['CODPRO'].astype(str).str.strip().str.zfill(6) == codigo_produto_formatado
                                        ]
                                        
                                        if not produto_planilha.empty:
                                            produto_row = produto_planilha.iloc[0]
                                            codigo_grupo = str(produto_row.get('CODCLA', '0001')).strip().zfill(4)
                                            codigo_fabricante = str(produto_row.get('CODFAB', '001')).strip().zfill(3)
                                            desc_produto = str(produto_row.get('DESCR', desc_produto)).strip()
                                    
                                    # Buscar/criar grupo
                                    if 'classes' in planilhas_aux:
                                        df_classes = planilhas_aux['classes']
                                        classe_planilha = df_classes[
                                            df_classes['CODCLA'].astype(str).str.strip().str.zfill(4) == codigo_grupo
                                        ]
                                        if not classe_planilha.empty:
                                            desc_grupo = str(classe_planilha.iloc[0].get('DESCR', desc_grupo)).strip()
                                    
                                    grupo, grupo_criado = GrupoProduto.objects.get_or_create(
                                        codigo=codigo_grupo,
                                        defaults={'descricao': desc_grupo[:100]}
                                    )
                                    if grupo_criado:
                                        grupos_criados += 1
                                    
                                    # Buscar/criar fabricante
                                    if 'fabricantes' in planilhas_aux:
                                        df_fabricantes = planilhas_aux['fabricantes']
                                        fab_planilha = df_fabricantes[
                                            df_fabricantes['CODFAB'].astype(str).str.strip().str.zfill(3) == codigo_fabricante
                                        ]
                                        if not fab_planilha.empty:
                                            desc_fabricante = str(fab_planilha.iloc[0].get('DESCR', desc_fabricante)).strip()
                                    
                                    fabricante, fab_criado = Fabricante.objects.get_or_create(
                                        codigo=codigo_fabricante,
                                        defaults={'descricao': desc_fabricante[:100]}
                                    )
                                    if fab_criado:
                                        fabricantes_criados += 1
                                    
                                    # Criar produto
                                    produto = Produto.objects.create(
                                        codigo=codigo_produto_formatado,
                                        descricao=desc_produto[:200],
                                        grupo=grupo,
                                        fabricante=fabricante
                                    )
                                    produtos_criados += 1
                            
                            if not produto:
                                erros.append(f"Linha {index + 2}: Produto não encontrado/criado")
                                continue
                            
                            # === CRIAR/BUSCAR LOJA E VENDEDOR ===
                            loja, loja_criada = Loja.objects.get_or_create(
                                codigo=codigo_loja,
                                defaults={'nome': f'Loja {codigo_loja}'}
                            )
                            if loja_criada:
                                lojas_criadas += 1
                            
                            nome_vendedor = str(row.get('VEND', 'VENDEDOR PADRÃO')).strip()
                            vendedor, vendedor_criado = Vendedor.objects.get_or_create(
                                codigo=codigo_vendedor.zfill(3),
                                defaults={'nome': nome_vendedor[:100], 'loja': loja}
                            )
                            if vendedor_criado:
                                vendedores_criados += 1
                            
                            # === CRIAR VENDA ===
                            try:
                                quantidade = Decimal(str(row['QTD']).replace(',', '.')) if pd.notna(row['QTD']) else Decimal('1')
                                valor_total = Decimal(str(row['TOTAL']).replace(',', '.')) if pd.notna(row['TOTAL']) else Decimal('0')
                            except (ValueError, TypeError):
                                erros.append(f"Linha {index + 2}: Valores numéricos inválidos")
                                continue
                            
                            # Processar data
                            try:
                                if 'data_convertida' in df_processamento.columns:
                                    # Usar data já convertida pelo filtro
                                    data_venda = row['data_convertida']
                                elif 'ANOMES' in row and pd.notna(row['ANOMES']):
                                    anomes = str(row['ANOMES']).strip()
                                    if len(anomes) == 4 and anomes.isdigit():
                                        ano_completo = '20' + anomes[:2]
                                        mes_num = anomes[2:]
                                        data_venda = datetime.strptime(f"{ano_completo}-{mes_num}-01", '%Y-%m-%d').date()
                                    else:
                                        data_venda = date(2024, 1, 1)
                                else:
                                    data_venda = date(2024, 1, 1)
                            except (ValueError, TypeError):
                                data_venda = date(2024, 1, 1)
                            
                            numero_nf = str(int(float(row['NF']))) if pd.notna(row['NF']) and row['NF'] != '' else ''
                            vendedor_nf = str(row.get('CLIVEN', '')).strip() if 'CLIVEN' in row else codigo_vendedor
                            uf = str(row.get('UF', 'SP')).strip()
                            
                            venda = Vendas.objects.create(
                                data_venda=data_venda,
                                cliente=cliente,
                                produto=produto,
                                grupo_produto=grupo,
                                fabricante=fabricante,
                                loja=loja,
                                quantidade=quantidade,
                                valor_total=valor_total,
                                numero_nf=numero_nf,
                                estado=uf,
                                vendedor_nf=vendedor_nf
                            )
                            vendas_criadas += 1
                            
                    except Exception as e:
                        erros.append(f"Linha {index + 2}: {str(e)}")
                        continue
                
                # ===== MENSAGEM DE RESULTADO COMPLETO =====
                total_processados = len(df_processamento)
                if vendas_criadas > 0:
                    messages.success(request, 
                        f"✅ IMPORTAÇÃO COMPLETA! "
                        f"{vendas_criadas} vendas importadas de {total_processados} registros processados."
                    )
                    
                    # Mostrar estatísticas dos novos registros criados
                    if clientes_criados + produtos_criados + grupos_criados + fabricantes_criados > 0:
                        detalhes = []
                        if clientes_criados > 0:
                            detalhes.append(f"{clientes_criados} clientes")
                        if produtos_criados > 0:
                            detalhes.append(f"{produtos_criados} produtos")
                        if grupos_criados > 0:
                            detalhes.append(f"{grupos_criados} grupos")
                        if fabricantes_criados > 0:
                            detalhes.append(f"{fabricantes_criados} fabricantes")
                        if lojas_criadas > 0:
                            detalhes.append(f"{lojas_criadas} lojas")
                        if vendedores_criados > 0:
                            detalhes.append(f"{vendedores_criados} vendedores")
                        
                        messages.info(request, f"📈 Novos registros criados: {', '.join(detalhes)}")
                else:
                    messages.warning(request, "⚠️ Nenhuma venda foi processada com sucesso.")
                
                if erros:
                    messages.warning(request, f"⚠️ {len(erros)} linhas com erro foram ignoradas.")
                    # Mostrar apenas os primeiros 5 erros para não poluir a tela
                    for erro in erros[:5]:
                        messages.error(request, erro)
                    if len(erros) > 5:
                        messages.info(request, f"... e mais {len(erros) - 5} erros similares")
                
                return redirect('gestor:vendas_list')
                
            except Exception as e:
                logger.error(f"Erro na importação BI: {str(e)}")
                messages.error(request, f'❌ Erro ao processar arquivo: {str(e)}')
    else:
        form = ImportarVendasForm()
    
    context = {'form': form, 'title': 'Importar Dados do BI'}
    return render(request, 'gestor/importar_vendas.html', context)