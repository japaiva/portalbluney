# core/management/commands/atualizar_vendedores.py

import os
import pandas as pd
import logging
from datetime import datetime
from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from core.models import Cliente, Vendedor, LogSincronizacao

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Atualiza vendedores dos clientes baseado no arquivo Excel listare.xlsx'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--arquivo',
            type=str,
            default='listare.xlsx',
            help='Caminho para o arquivo Excel (padrão: listare.xlsx)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executar em modo teste (não faz alterações)'
        )
        parser.add_argument(
            '--verificar-vendedores',
            action='store_true',
            help='Verificar se todos os vendedores existem antes de atualizar'
        )
        parser.add_argument(
            '--mostrar-detalhes',
            action='store_true',
            help='Mostrar detalhes de cada atualização'
        )
    
    def handle(self, *args, **options):
        arquivo_excel = options['arquivo']
        dry_run = options['dry_run']
        verificar_vendedores = options['verificar_vendedores']
        mostrar_detalhes = options['mostrar_detalhes']
        
        self.stdout.write(
            self.style.HTTP_INFO(f'🚀 Iniciando atualização de vendedores...')
        )
        
        # Verificar se arquivo existe
        if not os.path.exists(arquivo_excel):
            raise CommandError(f'❌ Arquivo não encontrado: {arquivo_excel}')
        
        self.stdout.write(f'📁 Lendo arquivo: {arquivo_excel}')
        
        # Criar log de sincronização
        log_sync = LogSincronizacao.objects.create(
            tipo='receita',
            status='iniciado',
            mensagem=f'Atualização de vendedores via {arquivo_excel}'
        )
        
        try:
            # Ler arquivo Excel
            df = pd.read_excel(arquivo_excel, sheet_name='Planilha2')
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Arquivo lido: {len(df)} registros encontrados')
            )
            
            # Verificar colunas necessárias
            colunas_necessarias = ['codcli', 'VEND']
            colunas_faltantes = [col for col in colunas_necessarias if col not in df.columns]
            
            if colunas_faltantes:
                raise CommandError(f'❌ Colunas faltantes: {colunas_faltantes}')
            
            # Limpar dados
            total_original = len(df)
            df_limpo = df.dropna(subset=['codcli', 'VEND']).copy()
            
            # Converter e formatar
            df_limpo['codcli'] = df_limpo['codcli'].astype(str)
            df_limpo['VEND'] = df_limpo['VEND'].astype(str).str.zfill(3)
            
            registros_removidos = total_original - len(df_limpo)
            if registros_removidos > 0:
                self.stdout.write(
                    self.style.WARNING(f'🧹 Removidos {registros_removidos} registros inválidos')
                )
            
            self.stdout.write(f'📋 Processando {len(df_limpo)} registros válidos')
            
            # Verificar vendedores se solicitado
            if verificar_vendedores:
                self._verificar_vendedores(df_limpo)
            
            # Processar atualizações
            resultado = self._processar_atualizacoes(
                df_limpo, dry_run, mostrar_detalhes, log_sync
            )
            
            # Finalizar log
            self._finalizar_log(log_sync, resultado)
            
            # Mostrar resultado final
            self._mostrar_resultado_final(resultado, dry_run)
            
        except Exception as e:
            erro_msg = f'❌ Erro durante execução: {str(e)}'
            self.stdout.write(self.style.ERROR(erro_msg))
            
            log_sync.status = 'erro'
            log_sync.mensagem = erro_msg
            log_sync.data_termino = datetime.now()
            log_sync.save()
            
            raise CommandError(erro_msg)
    
    def _verificar_vendedores(self, df_limpo):
        """Verificar se todos os vendedores existem no sistema"""
        self.stdout.write('🔍 Verificando vendedores no sistema...')
        
        vendedores_unicos = df_limpo['VEND'].unique()
        vendedores_existentes = set(
            Vendedor.objects.filter(
                codigo__in=vendedores_unicos
            ).values_list('codigo', flat=True)
        )
        
        vendedores_nao_encontrados = [
            v for v in vendedores_unicos 
            if v not in vendedores_existentes
        ]
        
        if vendedores_nao_encontrados:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️ Vendedores não cadastrados ({len(vendedores_nao_encontrados)}): '
                    f'{vendedores_nao_encontrados[:10]}...' if len(vendedores_nao_encontrados) > 10 
                    else f'{vendedores_nao_encontrados}'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('✅ Todos os vendedores estão cadastrados')
            )
    
    def _processar_atualizacoes(self, df_limpo, dry_run, mostrar_detalhes, log_sync):
        """Processar as atualizações dos vendedores"""
        resultado = {
            'processados': 0,
            'atualizados': 0,
            'nao_encontrados': 0,
            'sem_mudanca': 0,
            'erros': 0,
            'detalhes': []
        }
        
        self.stdout.write('🔄 Iniciando processamento...')
        
        with transaction.atomic():
            for index, row in df_limpo.iterrows():
                codigo_cliente = str(row['codcli'])
                codigo_vendedor = str(row['VEND']).zfill(3)
                nome_cliente = str(row.get('NOME', 'N/A'))[:50]
                
                resultado['processados'] += 1
                
                try:
                    # Buscar cliente
                    cliente = Cliente.objects.filter(codigo=codigo_cliente).first()
                    
                    if not cliente:
                        resultado['nao_encontrados'] += 1
                        detalhe = f'⚠️ Cliente não encontrado: {codigo_cliente}'
                        resultado['detalhes'].append(detalhe)
                        
                        if mostrar_detalhes or resultado['nao_encontrados'] <= 5:
                            self.stdout.write(self.style.WARNING(detalhe))
                        continue
                    
                    # Verificar se há mudança
                    vendedor_atual = cliente.codigo_vendedor or ''
                    if vendedor_atual == codigo_vendedor:
                        resultado['sem_mudanca'] += 1
                        continue
                    
                    # Fazer atualização
                    if not dry_run:
                        cliente.codigo_vendedor = codigo_vendedor
                        cliente.save()
                        cliente.limpar_cache_vendedor()
                    
                    resultado['atualizados'] += 1
                    
                    detalhe = (
                        f'✅ {codigo_cliente} ({nome_cliente}): '
                        f'{vendedor_atual or "vazio"} → {codigo_vendedor}'
                    )
                    resultado['detalhes'].append(detalhe)
                    
                    if mostrar_detalhes or resultado['atualizados'] <= 10:
                        self.stdout.write(detalhe)
                
                except Exception as e:
                    resultado['erros'] += 1
                    detalhe = f'❌ Erro cliente {codigo_cliente}: {str(e)}'
                    resultado['detalhes'].append(detalhe)
                    
                    if mostrar_detalhes or resultado['erros'] <= 5:
                        self.stdout.write(self.style.ERROR(detalhe))
                
                # Mostrar progresso a cada 100 registros
                if resultado['processados'] % 100 == 0:
                    self.stdout.write(f'📊 Processados: {resultado["processados"]}')
            
            # Rollback se for dry-run
            if dry_run:
                transaction.set_rollback(True)
                self.stdout.write(
                    self.style.WARNING('🔍 MODO TESTE - Nenhuma alteração foi salva')
                )
        
        return resultado
    
    def _finalizar_log(self, log_sync, resultado):
        """Finalizar o log de sincronização"""
        log_sync.registros_processados = resultado['processados']
        log_sync.registros_atualizados = resultado['atualizados']
        log_sync.registros_com_erro = resultado['erros'] + resultado['nao_encontrados']
        log_sync.status = 'concluido' if resultado['erros'] == 0 else 'concluido_com_erros'
        log_sync.data_termino = datetime.now()
        
        # Resumo dos primeiros detalhes
        primeiros_detalhes = resultado['detalhes'][:20]
        if len(resultado['detalhes']) > 20:
            primeiros_detalhes.append(f'... e mais {len(resultado["detalhes"]) - 20} registros')
        
        log_sync.mensagem = '\n'.join(primeiros_detalhes)
        log_sync.save()
    
    def _mostrar_resultado_final(self, resultado, dry_run):
        """Mostrar o resultado final da execução"""
        self.stdout.write(
            self.style.SUCCESS('\n' + '=' * 50)
        )
        self.stdout.write(
            self.style.SUCCESS('📊 RELATÓRIO FINAL')
        )
        self.stdout.write(
            self.style.SUCCESS('=' * 50)
        )
        
        self.stdout.write(f'📋 Registros processados: {resultado["processados"]:,}')
        self.stdout.write(
            self.style.SUCCESS(f'✅ Clientes atualizados: {resultado["atualizados"]:,}')
        )
        self.stdout.write(f'⏭️ Clientes sem mudança: {resultado["sem_mudanca"]:,}')
        self.stdout.write(
            self.style.WARNING(f'⚠️ Clientes não encontrados: {resultado["nao_encontrados"]:,}')
        )
        
        if resultado['erros'] > 0:
            self.stdout.write(
                self.style.ERROR(f'❌ Erros: {resultado["erros"]:,}')
            )
        
        self.stdout.write('=' * 50)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️ MODO TESTE ATIVO\n'
                    'Execute novamente sem --dry-run para aplicar as alterações'
                )
            )
        elif resultado['atualizados'] > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🎉 Atualização concluída!\n'
                    f'{resultado["atualizados"]} clientes tiveram seus vendedores atualizados.'
                )
            )
            
            # Limpar cache geral
            self.stdout.write('🧹 Limpando cache de vendedores...')
            cache_limpos = Cliente.limpar_cache_vendedores()
            self.stdout.write(f'✅ Cache limpo para {cache_limpos} códigos de vendedores')