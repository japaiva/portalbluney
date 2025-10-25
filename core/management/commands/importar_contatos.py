# core/management/commands/importar_contatos.py
"""
Django Management Command para importar contatos de clientes

Uso:
    python manage.py importar_contatos
    python manage.py importar_contatos --dry-run
    python manage.py importar_contatos --verificar
    python manage.py importar_contatos --arquivo /caminho/arquivo.xlsx
    python manage.py importar_contatos --limpar
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core.models import Cliente, ClienteContato
import pandas as pd
import os


class Command(BaseCommand):
    help = 'Importa contatos de clientes a partir de um arquivo Excel'

    def add_arguments(self, parser):
        parser.add_argument(
            '--arquivo',
            type=str,
            help='Nome do arquivo Excel (padrão: cliente_contato_para_importar.xlsx)',
            default='cliente_contato_para_importar.xlsx'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa simulação sem salvar no banco de dados',
        )
        parser.add_argument(
            '--limpar',
            action='store_true',
            help='Remove todos os contatos existentes antes de importar',
        )
        parser.add_argument(
            '--verificar',
            action='store_true',
            help='Apenas verifica clientes faltantes, não importa',
        )
        parser.add_argument(
            '--pular-faltantes',
            action='store_true',
            help='Pula clientes que não existem no banco (não gera erro)',
        )

    def handle(self, *args, **options):
        arquivo = options['arquivo']
        dry_run = options['dry_run']
        limpar = options['limpar']
        verificar = options['verificar']
        pular_faltantes = options['pular_faltantes']

        # Verificar se arquivo existe
        if not os.path.exists(arquivo):
            raise CommandError(f'Arquivo não encontrado: {arquivo}\nColoque o arquivo na raiz do projeto ou use --arquivo /caminho/completo')

        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS('IMPORTAÇÃO DE CONTATOS DE CLIENTES'))
        self.stdout.write("=" * 80)

        # Modo de execução
        if dry_run:
            self.stdout.write(self.style.WARNING('\n🔍 MODO: DRY RUN (simulação)'))
        else:
            self.stdout.write(self.style.SUCCESS('\n💾 MODO: IMPORTAÇÃO REAL'))

        self.stdout.write(f'📂 Arquivo: {arquivo}')

        # Carregar dados
        self.stdout.write('\n📊 Carregando dados...')
        try:
            df = pd.read_excel(arquivo)
        except Exception as e:
            raise CommandError(f'Erro ao carregar arquivo: {e}')

        self.stdout.write(self.style.SUCCESS(f'✅ Dados carregados: {len(df)} registros'))
        self.stdout.write(f'   Clientes únicos: {df["Codigo"].nunique()}')
        self.stdout.write(f'   Contatos principais: {df["Principal"].sum()}')
        self.stdout.write(f'   Contatos secundários: {(~df["Principal"]).sum()}')

        # Se apenas verificar
        if verificar:
            self.verificar_clientes(df)
            return

        # Limpar contatos existentes se solicitado
        if limpar and not dry_run:
            self.limpar_contatos()

        # Importar contatos
        self.importar_contatos(df, dry_run, pular_faltantes)

    def verificar_clientes(self, df):
        """Verifica quais clientes do Excel existem no banco"""
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("🔍 VERIFICAÇÃO DE CLIENTES")
        self.stdout.write("=" * 80)

        codigos_excel = df['Codigo'].unique()
        self.stdout.write(f'\nClientes no Excel: {len(codigos_excel)}')

        # Buscar clientes existentes
        clientes_existentes = set(
            Cliente.objects.filter(
                codigo__in=[str(c) for c in codigos_excel]
            ).values_list('codigo', flat=True)
        )

        codigos_faltantes = [
            str(c) for c in codigos_excel 
            if str(c) not in clientes_existentes
        ]

        self.stdout.write(f'Clientes no banco: {len(clientes_existentes)}')
        self.stdout.write(f'Clientes FALTANTES: {len(codigos_faltantes)}')

        if codigos_faltantes:
            self.stdout.write(self.style.WARNING(
                '\n⚠️  Clientes que precisam ser cadastrados primeiro:'
            ))
            
            # Mostrar até 30 clientes faltantes
            for cod in sorted(codigos_faltantes[:30]):
                # Buscar empresa correspondente (cod pode ser string, comparar com valor original)
                linha = df[df['Codigo'].astype(str) == cod]
                if not linha.empty:
                    empresa = linha['Empresa'].iloc[0]
                    self.stdout.write(f'  - {cod}: {empresa[:60]}')
                else:
                    self.stdout.write(f'  - {cod}: (empresa não encontrada)')
            
            if len(codigos_faltantes) > 30:
                self.stdout.write(f'\n... e mais {len(codigos_faltantes) - 30} clientes')
                self.stdout.write(f'\n💡 Dica: Cadastre estes clientes antes de importar os contatos')
        else:
            self.stdout.write(self.style.SUCCESS(
                '\n✅ Todos os clientes existem no banco!'
            ))

    def limpar_contatos(self):
        """Remove todos os contatos existentes"""
        contatos_count = ClienteContato.objects.count()
        
        if contatos_count == 0:
            self.stdout.write('ℹ️  Nenhum contato existente para limpar')
            return

        self.stdout.write(self.style.WARNING(
            f'\n⚠️  ATENÇÃO: Excluindo {contatos_count} contatos existentes...'
        ))
        
        ClienteContato.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('✅ Contatos excluídos!'))

    def importar_contatos(self, df, dry_run, pular_faltantes=False):
        """Importa os contatos do DataFrame"""
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("🔄 PROCESSANDO CONTATOS...")
        self.stdout.write("=" * 80)
        
        if pular_faltantes:
            self.stdout.write(self.style.WARNING('⚠️  Modo: Pulando clientes não encontrados\n'))

        stats = {
            'total': len(df),
            'processados': 0,
            'criados': 0,
            'atualizados': 0,
            'erros': 0,
            'cliente_nao_encontrado': 0,
            'pulados': 0,
        }

        erros = []

        # Processar em transação se não for dry_run
        if not dry_run:
            with transaction.atomic():
                stats, erros = self._processar_registros(df, stats, erros, dry_run, pular_faltantes)
        else:
            stats, erros = self._processar_registros(df, stats, erros, dry_run, pular_faltantes)

        # Relatório final
        self._exibir_relatorio(stats, erros, dry_run)

    def _processar_registros(self, df, stats, erros, dry_run, pular_faltantes=False):
        """Processa cada registro do DataFrame"""
        
        for idx, row in df.iterrows():
            stats['processados'] += 1

            try:
                codigo_cliente = str(row['Codigo']).strip()
                whatsapp = str(row['Whatsapp']).strip()
                nome_contato = str(row['Nome_Contato']).strip() if pd.notna(row['Nome_Contato']) else ''
                eh_principal = bool(row['Principal'])

                if dry_run:
                    # Simulação - apenas validar se cliente existe
                    if not Cliente.objects.filter(codigo=codigo_cliente).exists():
                        stats['cliente_nao_encontrado'] += 1
                        if pular_faltantes:
                            stats['pulados'] += 1
                        else:
                            erros.append({
                                'linha': idx + 2,
                                'codigo': codigo_cliente,
                                'erro': f'Cliente não encontrado'
                            })
                    else:
                        stats['criados'] += 1
                else:
                    # Importação real
                    try:
                        cliente = Cliente.objects.get(codigo=codigo_cliente)
                    except Cliente.DoesNotExist:
                        stats['cliente_nao_encontrado'] += 1
                        if pular_faltantes:
                            stats['pulados'] += 1
                            continue  # Pula para o próximo
                        else:
                            erros.append({
                                'linha': idx + 2,
                                'codigo': codigo_cliente,
                                'erro': 'Cliente não encontrado no banco'
                            })
                            continue

                    # Verificar se já existe
                    contato_existente = ClienteContato.objects.filter(
                        cliente=cliente,
                        whatsapp=whatsapp
                    ).first()

                    if contato_existente:
                        # Atualizar
                        contato_existente.nome = nome_contato
                        contato_existente.principal = eh_principal
                        contato_existente.ativo = True
                        contato_existente.save()
                        stats['atualizados'] += 1
                    else:
                        # Criar novo
                        ClienteContato.objects.create(
                            cliente=cliente,
                            codigo=codigo_cliente,
                            codigo_master=codigo_cliente,
                            whatsapp=whatsapp,
                            nome=nome_contato,
                            principal=eh_principal,
                            ativo=True
                        )
                        stats['criados'] += 1

            except Exception as e:
                stats['erros'] += 1
                erros.append({
                    'linha': idx + 2,
                    'codigo': codigo_cliente if 'codigo_cliente' in locals() else 'N/A',
                    'erro': str(e)
                })

            # Progress
            if (idx + 1) % 100 == 0:
                self.stdout.write(f'   Processados: {idx + 1}/{len(df)}...')

        return stats, erros

    def _exibir_relatorio(self, stats, erros, dry_run):
        """Exibe relatório final da importação"""
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS('📊 RELATÓRIO FINAL'))
        self.stdout.write("=" * 80)

        self.stdout.write(f'\nTotal processados: {stats["processados"]}')
        self.stdout.write(self.style.SUCCESS(f'  ✅ Criados: {stats["criados"]}'))
        
        if stats['atualizados'] > 0:
            self.stdout.write(self.style.WARNING(f'  🔄 Atualizados: {stats["atualizados"]}'))
        
        if stats.get('pulados', 0) > 0:
            self.stdout.write(self.style.WARNING(f'  ⏭️  Pulados (cliente não existe): {stats["pulados"]}'))
        
        if stats['erros'] > 0:
            self.stdout.write(self.style.ERROR(f'  ❌ Erros: {stats["erros"]}'))
        
        if stats['cliente_nao_encontrado'] > 0 and stats.get('pulados', 0) == 0:
            self.stdout.write(self.style.WARNING(
                f'  ⚠️  Clientes não encontrados: {stats["cliente_nao_encontrado"]}'
            ))

        # Mostrar erros
        if erros:
            self.stdout.write("\n" + "=" * 80)
            self.stdout.write(self.style.ERROR('❌ ERROS ENCONTRADOS'))
            self.stdout.write("=" * 80)
            
            for erro in erros[:20]:
                self.stdout.write(f'\nLinha {erro["linha"]}:')
                self.stdout.write(f'  Cliente: {erro["codigo"]}')
                self.stdout.write(f'  Erro: {erro["erro"]}')
            
            if len(erros) > 20:
                self.stdout.write(f'\n... e mais {len(erros) - 20} erros')

        # Mensagem final
        self.stdout.write("\n" + "=" * 80)
        if dry_run:
            self.stdout.write(self.style.SUCCESS('✅ SIMULAÇÃO CONCLUÍDA!'))
            self.stdout.write('\n💡 Para importar de verdade, remova o --dry-run')
        else:
            self.stdout.write(self.style.SUCCESS('✅ IMPORTAÇÃO CONCLUÍDA!'))
        self.stdout.write("=" * 80)