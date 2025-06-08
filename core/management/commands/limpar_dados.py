# ===== ARQUIVO: gestor/management/commands/limpar_dados.py =====

from django.core.management.base import BaseCommand
from core.models import Vendas, GrupoProduto, Fabricante, Produto

class Command(BaseCommand):
    help = 'Limpa dados de vendas, grupos, fabricantes e produtos'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Confirma a exclusão dos dados',
        )
        parser.add_argument(
            '--apenas-vendas',
            action='store_true',
            help='Exclui apenas as vendas, mantendo produtos/grupos/fabricantes',
        )
    
    def handle(self, *args, **options):
        if not options['confirmar']:
            self.stdout.write(
                self.style.WARNING(
                    '⚠️ ATENÇÃO: Este comando irá excluir dados!\n\n'
                    'OPÇÕES:\n'
                    '1. Limpeza completa (vendas + produtos + grupos + fabricantes):\n'
                    '   python manage.py limpar_dados --confirmar\n\n'
                    '2. Apenas vendas (mantém produtos/grupos/fabricantes):\n'
                    '   python manage.py limpar_dados --apenas-vendas --confirmar\n'
                )
            )
            return
        
        # Contar registros antes
        vendas_count = Vendas.objects.count()
        produtos_count = Produto.objects.count()
        grupos_count = GrupoProduto.objects.count()
        fabricantes_count = Fabricante.objects.count()
        
        self.stdout.write(self.style.HTTP_INFO('📊 Registros encontrados:'))
        self.stdout.write(f'   Vendas: {vendas_count}')
        self.stdout.write(f'   Produtos: {produtos_count}')
        self.stdout.write(f'   Grupos: {grupos_count}')
        self.stdout.write(f'   Fabricantes: {fabricantes_count}')
        
        if options['apenas_vendas']:
            # Excluir apenas vendas
            self.stdout.write('\n🗑️ Excluindo apenas VENDAS...')
            Vendas.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'✅ {vendas_count} vendas excluídas'))
            self.stdout.write(self.style.SUCCESS('🎉 Vendas limpas! Produtos mantidos.'))
        else:
            # Excluir tudo em ordem (vendas primeiro por causa das FKs)
            self.stdout.write('\n🗑️ Excluindo TODOS os dados...')
            
            if vendas_count > 0:
                Vendas.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'✅ {vendas_count} vendas excluídas'))
            
            if produtos_count > 0:
                Produto.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'✅ {produtos_count} produtos excluídos'))
            
            if grupos_count > 0:
                GrupoProduto.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'✅ {grupos_count} grupos excluídos'))
            
            if fabricantes_count > 0:
                Fabricante.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'✅ {fabricantes_count} fabricantes excluídos'))
            
            self.stdout.write(self.style.SUCCESS('\n🎉 Limpeza completa concluída!'))
        
        # Mostrar resumo final
        vendas_final = Vendas.objects.count()
        produtos_final = Produto.objects.count()
        grupos_final = GrupoProduto.objects.count()
        fabricantes_final = Fabricante.objects.count()
        
        self.stdout.write(self.style.HTTP_INFO('\n📊 Registros após limpeza:'))
        self.stdout.write(f'   Vendas: {vendas_final}')
        self.stdout.write(f'   Produtos: {produtos_final}')
        self.stdout.write(f'   Grupos: {grupos_final}')
        self.stdout.write(f'   Fabricantes: {fabricantes_final}')