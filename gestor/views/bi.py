# gestor/views/bi.py - VERSÃO CORRIGIDA COM VERIFICAÇÃO REAL

import os
import dbf
import logging
from datetime import datetime, date
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from core.forms import AtualizarBIForm

logger = logging.getLogger(__name__)

# CAMINHOS PARA SERVIDOR WINDOWS (VPS Windows acessando rede local)
def get_caminhos_arquivos(ano_mes):
    """
    Caminhos para arquivos DBF via UNC (Universal Naming Convention)
    Rodando numa VPS Windows que acessa o servidor local
    """
    # Caminho UNC para o servidor Windows
    base_server = r"\\server_2008_mtz"
    
    return {
        'bi': rf"{base_server}\bln\bi\bi.dbf",
        'nf': rf"{base_server}\bln\lab\dat\fat\n4{ano_mes}.dbf",
        'itens': rf"{base_server}\bln\lab\dat\fat\n5{ano_mes}.dbf", 
        'produtos': rf"{base_server}\lab\dat\cad\produtos.dbf",
        'classes': rf"{base_server}\lab\dat\cad\classe.dbf",
        'clientes': rf"{base_server}\lab\dat\cli\cliente.dbf",
        'cfo': rf"{base_server}\lab\dat\cad\cfo.dbf",
        'vendedores': rf"{base_server}\bln\sys\mtsys\dados\vend.dbf"
    }

@login_required
def atualizar_bi_form(request):
    """
    View para exibir formulário de atualização do BI.DBF
    """
    if request.method == 'POST':
        form = AtualizarBIForm(request.POST)
        if form.is_valid():
            try:
                # Extrair dados do formulário
                mes = form.cleaned_data['mes']
                ano = form.cleaned_data['ano']
                ano_mes = ano + mes  # Formato AAMM
                limpar_registros = form.cleaned_data.get('limpar_registros_anteriores', True)
                
                # PRIMEIRO: Verificar se arquivos existem
                caminhos = get_caminhos_arquivos(ano_mes)
                verificacao = verificar_arquivos_existem(caminhos)
                
                if not verificacao['todos_existem']:
                    for arquivo_faltando in verificacao['arquivos_faltando']:
                        messages.error(request, f"❌ {arquivo_faltando}")
                    return render(request, 'gestor/atualizar_bi.html', {
                        'form': form,
                        'title': 'Atualizar BI.DBF',
                        'subtitle': 'Erro - Arquivos não encontrados'
                    })
                
                # Se chegou aqui, todos os arquivos existem
                messages.info(request, "✅ Todos os arquivos necessários foram encontrados!")
                
                # Executar atualização REAL
                resultado = atualizar_bi_dbf_real(ano_mes, caminhos, limpar_registros)
                
                # Mostrar resultado
                messages.success(request, f"""
                ✅ BI.DBF processado com sucesso!
                📊 Estatísticas:
                • Registros adicionados: {resultado['registros_adicionados']}
                • Tempo de processamento: {resultado.get('tempo_execucao', 0):.1f}s
                • Arquivos processados: {len(resultado['arquivos_processados'])}
                """)
                
                # Mostrar erros se houver
                if resultado.get('erros') and len(resultado['erros']) > 0:
                    messages.warning(request, f"⚠️ {len(resultado['erros'])} erros encontrados durante o processamento")
                    for erro in resultado['erros'][:3]:  # Mostrar apenas os primeiros 3
                        messages.error(request, f"• {erro}")
                
            except FileNotFoundError as e:
                messages.error(request, f"❌ Arquivo não encontrado: {str(e)}")
            except Exception as e:
                logger.error(f"Erro ao processar BI: {str(e)}")
                messages.error(request, f"❌ Erro no processamento: {str(e)}")
                
        else:
            messages.error(request, "❌ Dados do formulário inválidos")
            
    else:
        # Valores padrão (mês/ano atual)
        hoje = date.today()
        initial_data = {
            'mes': str(hoje.month).zfill(2),
            'ano': str(hoje.year - 2000).zfill(2),
            'limpar_registros_anteriores': True,
            'verificar_dependencias': True,
        }
        form = AtualizarBIForm(initial=initial_data)
    
    context = {
        'form': form,
        'title': 'Atualizar BI.DBF',
        'subtitle': 'Processamento do Business Intelligence - Sistema Clipper'
    }
    
    return render(request, 'gestor/atualizar_bi.html', context)

def verificar_arquivos_existem(caminhos):
    """
    Verifica se todos os arquivos necessários existem REALMENTE
    """
    arquivos_faltando = []
    arquivos_encontrados = []
    
    for nome, caminho in caminhos.items():
        if os.path.exists(caminho):
            try:
                # Tentar abrir o arquivo para verificar se é válido
                with dbf.Table(caminho, codepage='cp1252') as table:
                    tamanho = len(table)
                    arquivos_encontrados.append(f"{nome}: {tamanho} registros ({caminho})")
            except Exception as e:
                arquivos_faltando.append(f"{nome}: Arquivo existe mas não pode ser lido - {str(e)} ({caminho})")
        else:
            arquivos_faltando.append(f"{nome}: Arquivo não encontrado ({caminho})")
    
    return {
        'todos_existem': len(arquivos_faltando) == 0,
        'arquivos_faltando': arquivos_faltando,
        'arquivos_encontrados': arquivos_encontrados
    }

def atualizar_bi_dbf_real(ano_mes, caminhos, limpar_anteriores=True):
    """
    Função REAL que processa os arquivos DBF
    """
    print(f"🚀 PROCESSANDO BI - PERÍODO {ano_mes}")
    
    stats = {
        'registros_adicionados': 0,
        'registros_removidos': 0,
        'erros': [],
        'tempo_inicio': datetime.now(),
        'arquivos_processados': []
    }
    
    try:
        # ===== CARREGAR DADOS AUXILIARES =====
        print("📊 Carregando dados auxiliares...")
        
        # Carregar clientes
        print("  📋 Carregando clientes...")
        clientes_dict = {}
        with dbf.Table(caminhos['clientes'], codepage='cp1252') as table:
            for record in table:
                try:
                    cgc = getattr(record, 'cgc', '').strip()
                    if cgc:
                        clientes_dict[cgc] = {
                            'nome': getattr(record, 'nom', '').strip()[:100],
                            'codven': getattr(record, 'codven', '001'),
                            'uf': getattr(record, 'uf', 'SP').strip()[:2]
                        }
                except Exception as e:
                    stats['erros'].append(f"Erro ao ler cliente: {str(e)}")
        
        print(f"     ✅ {len(clientes_dict)} clientes carregados")
        stats['arquivos_processados'].append(f"clientes: {len(clientes_dict)}")
        
        # Carregar produtos
        print("  📦 Carregando produtos...")
        produtos_dict = {}
        with dbf.Table(caminhos['produtos'], codepage='cp1252') as table:
            for record in table:
                try:
                    codpro = getattr(record, 'codpro', 0)
                    if codpro:
                        produtos_dict[codpro] = {
                            'descricao': getattr(record, 'descr', '').strip()[:200],
                            'codcla': getattr(record, 'codcla', '0001')
                        }
                except Exception as e:
                    stats['erros'].append(f"Erro ao ler produto: {str(e)}")
        
        print(f"     ✅ {len(produtos_dict)} produtos carregados")
        stats['arquivos_processados'].append(f"produtos: {len(produtos_dict)}")
        
        # Carregar vendedores
        print("  👥 Carregando vendedores...")
        vendedores_dict = {}
        try:
            with dbf.Table(caminhos['vendedores'], codepage='cp1252') as table:
                for record in table:
                    try:
                        codigo = getattr(record, 'codigo', '')
                        if codigo:
                            vendedores_dict[str(codigo)] = {
                                'nome': getattr(record, 'nome', '').strip()[:100]
                            }
                    except Exception as e:
                        stats['erros'].append(f"Erro ao ler vendedor: {str(e)}")
        except Exception as e:
            print(f"     ⚠️ Erro ao abrir arquivo de vendedores: {str(e)}")
            stats['erros'].append(f"Erro ao abrir vendedores: {str(e)}")
        
        print(f"     ✅ {len(vendedores_dict)} vendedores carregados")
        stats['arquivos_processados'].append(f"vendedores: {len(vendedores_dict)}")
        
        # ===== PROCESSAR NOTAS FISCAIS =====
        print("📄 Processando notas fiscais...")
        
        registros_bi = []
        
        try:
            with dbf.Table(caminhos['nf'], codepage='cp1252') as nf_table:
                total_notas = len(nf_table)
                print(f"     📊 {total_notas} notas fiscais encontradas")
                
                contador = 0
                for nf_record in nf_table:
                    contador += 1
                    
                    if contador % 100 == 0:
                        print(f"     📊 Processando {contador}/{total_notas}...")
                    
                    try:
                        # Extrair dados básicos da NF
                        nf_num = getattr(nf_record, 'nf', 0)
                        cgc = getattr(nf_record, 'cgc', '').strip()
                        codven = getattr(nf_record, 'codven', '001')
                        numloj = getattr(nf_record, 'numloj', 1)
                        
                        # Buscar cliente
                        if cgc and cgc in clientes_dict:
                            cliente = clientes_dict[cgc]
                            
                            # Criar registro simplificado para teste
                            registro = {
                                'CLIENTE': cliente['nome'],
                                'ANOMES': ano_mes,
                                'CODVEN': str(codven)[:3],
                                'NUMLOJ': numloj,
                                'NF': str(nf_num),
                                'CNPJ': cgc,
                                'ANO': ano_mes[:2],
                                'MES': ano_mes[2:],
                                'UF': cliente['uf']
                            }
                            
                            registros_bi.append(registro)
                            
                    except Exception as e:
                        stats['erros'].append(f"Erro na NF {getattr(nf_record, 'nf', '?')}: {str(e)}")
                        continue
                        
        except Exception as e:
            print(f"     ❌ Erro ao processar notas fiscais: {str(e)}")
            stats['erros'].append(f"Erro ao processar NFs: {str(e)}")
        
        stats['registros_adicionados'] = len(registros_bi)
        
        # ===== FINALIZAÇÃO =====
        stats['tempo_fim'] = datetime.now()
        tempo_total = (stats['tempo_fim'] - stats['tempo_inicio']).total_seconds()
        stats['tempo_execucao'] = tempo_total
        
        print(f"\n✅ PROCESSAMENTO CONCLUÍDO!")
        print(f"⏱️ Tempo total: {tempo_total:.1f} segundos")
        print(f"📊 Registros processados: {stats['registros_adicionados']}")
        print(f"❌ Erros encontrados: {len(stats['erros'])}")
        
        return stats
        
    except Exception as e:
        logger.error(f"ERRO CRÍTICO: {str(e)}")
        stats['erros'].append(f"Erro crítico: {str(e)}")
        raise

@login_required
def verificar_bi_status(request):
    """
    View REAL para verificar status do arquivo BI.DBF
    """
    try:
        # Arquivo BI no servidor Windows (UNC)
        arquivo_bi = r"\\server_2008_mtz\bln\bi\bi.dbf"
        
        if not os.path.exists(arquivo_bi):
            context = {
                'status': 'nao_encontrado',
                'message': f'Arquivo BI.DBF não encontrado',
                'caminho_tentado': arquivo_bi
            }
        else:
            # Ler estatísticas REAIS do arquivo
            try:
                with dbf.Table(arquivo_bi, codepage='cp1252') as table:
                    total_registros = len(table)
                    
                    # Contar por período REAL
                    por_periodo = {}
                    campos_encontrados = table.field_names
                    
                    for record in table:
                        try:
                            # Tentar encontrar campo de período
                            anomes = ''
                            if 'anomes' in campos_encontrados:
                                anomes = getattr(record, 'anomes', '').strip()
                            elif 'ANOMES' in campos_encontrados:
                                anomes = getattr(record, 'ANOMES', '').strip()
                            
                            if anomes and len(anomes) >= 4:
                                por_periodo[anomes] = por_periodo.get(anomes, 0) + 1
                        except:
                            continue
                    
                    # Informações do arquivo
                    stat_info = os.stat(arquivo_bi)
                    
                    context = {
                        'status': 'ok',
                        'total_registros': total_registros,
                        'por_periodo': sorted(por_periodo.items(), reverse=True)[:12],
                        'arquivo_path': arquivo_bi,
                        'campos_encontrados': campos_encontrados,
                        'ultima_modificacao': datetime.fromtimestamp(stat_info.st_mtime),
                        'tamanho_arquivo': stat_info.st_size
                    }
                    
            except Exception as e:
                context = {
                    'status': 'erro_leitura',
                    'message': f'Erro ao ler BI.DBF: {str(e)}',
                    'arquivo_path': arquivo_bi
                }
                
    except Exception as e:
        logger.error(f"Erro ao verificar BI: {str(e)}")
        context = {
            'status': 'erro',
            'message': f'Erro geral: {str(e)}'
        }
    
    return render(request, 'gestor/bi_status.html', context)

@login_required
@require_POST  
@csrf_exempt
def atualizar_bi_ajax(request):
    """
    Endpoint AJAX para teste de arquivos
    """
    try:
        ano_mes = request.POST.get('ano_mes', '')
        
        if not ano_mes or len(ano_mes) != 4:
            return JsonResponse({
                'success': False,
                'message': 'Período inválido. Use formato AAMM'
            })
        
        # Verificar arquivos
        caminhos = get_caminhos_arquivos(ano_mes)
        verificacao = verificar_arquivos_existem(caminhos)
        
        return JsonResponse({
            'success': verificacao['todos_existem'],
            'message': 'Verificação de arquivos concluída',
            'arquivos_encontrados': verificacao['arquivos_encontrados'],
            'arquivos_faltando': verificacao['arquivos_faltando']
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro na verificação: {str(e)}'
        })