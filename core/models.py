# core/models.py

import logging
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

class Usuario(AbstractUser):
    NIVEL_CHOICES = [
        ('admin', 'Admin'),
        ('gestor', 'Gestor'),
        ('vendedor', 'Vendedor'),
    ]

    # Desabilitar relacionamentos explicitamente
    groups = None  # Remove o relacionamento com grupos
    user_permissions = None  # Remove o relacionamento com permissões individuais
    
    nivel = models.CharField(max_length=20, choices=NIVEL_CHOICES)
    is_superuser = models.BooleanField(default=False)
    last_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    codigo_loja = models.CharField(max_length=3, blank=True, null=True, 
                                  help_text="Código de 3 dígitos da loja (NUMLOJ no SysFat)")
    codigo_vendedor = models.CharField(max_length=3, blank=True, null=True, 
                                      help_text="Código de 3 dígitos do vendedor (CODVEN no SysFat)")
    
    def __str__(self):
        return self.username
    
    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

class Parametro(models.Model):
    parametro = models.CharField(max_length=50)
    valor = models.FloatField()

    def __str__(self):
        return self.parametro
    
    class Meta:
        db_table = 'parametros'

class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil')
    telefone = models.CharField(max_length=20, blank=True, null=True)
    nivel = models.CharField(
        max_length=20,
        choices=[
            ('admin', 'Administrador'),
            ('gestor', 'Gestor'),
            ('projetista', 'Projetista'),
            ('cliente', 'Cliente'),
            ('vendedor', 'Vendedor'),
        ],
        default='cliente'
    )
    
    def __str__(self):
        return f"{self.usuario.username} - {self.get_nivel_display()}"

# ===== MODELOS DE CADASTRO BÁSICO =====

class Loja(models.Model):
    codigo = models.CharField(max_length=3, primary_key=True)
    nome = models.CharField(max_length=100)
    endereco = models.CharField(max_length=200, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)
    cep = models.CharField(max_length=10, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"
    
    class Meta:
        db_table = 'lojas'
        verbose_name = 'Loja'
        verbose_name_plural = 'Lojas'
        ordering = ['codigo']

class Vendedor(models.Model):
    codigo = models.CharField(max_length=3, primary_key=True)
    nome = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    ativo = models.BooleanField(default=True)
    loja = models.ForeignKey(Loja, on_delete=models.PROTECT, related_name='vendedores', null=True, blank=True)
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"
    
    class Meta:
        db_table = 'vendedores'
        verbose_name = 'Vendedor'
        verbose_name_plural = 'Vendedores'
        ordering = ['codigo']

class Fabricante(models.Model):
    codigo = models.CharField(max_length=10, primary_key=True)
    descricao = models.CharField(max_length=100)
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.codigo} - {self.descricao}"
    
    class Meta:
        db_table = 'fabricantes'
        verbose_name = 'Fabricante'
        verbose_name_plural = 'Fabricantes'
        ordering = ['codigo']

class GrupoProduto(models.Model):
    codigo = models.CharField(max_length=4, primary_key=True)
    descricao = models.CharField(max_length=100)
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.codigo} - {self.descricao}"
    
    class Meta:
        db_table = 'grupos_produto'
        verbose_name = 'Grupo de Produto'
        verbose_name_plural = 'Grupos de Produto'
        ordering = ['codigo']

class Produto(models.Model):
    codigo = models.CharField(max_length=6, primary_key=True)
    descricao = models.CharField(max_length=200)
    grupo = models.ForeignKey(GrupoProduto, on_delete=models.PROTECT, related_name='produtos')
    fabricante = models.ForeignKey(Fabricante, on_delete=models.PROTECT, related_name='produtos')
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.codigo} - {self.descricao}"
    
    class Meta:
        db_table = 'produtos'
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['codigo']

# ===== MODELO CLIENTE ATUALIZADO =====
class Cliente(models.Model):
    # Choices para Situação Cadastral da Receita Federal
    SITUACAO_CADASTRAL_CHOICES = [
        ('01', 'Nula'),
        ('02', 'Ativa'),
        ('03', 'Suspensa'),
        ('04', 'Inapta'),
        ('08', 'Baixada'),
        ('2.0', 'Ativa'),  # Compatibilidade com retornos da API
        ('3.0', 'Suspensa'),
        ('4.0', 'Inapta'),
        ('8.0', 'Baixada'),
    ]
    
    # *** ATUALIZADO: STATUS COM "OUTROS" ***
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('inativo', 'Inativo'),
        ('rascunho', 'Rascunho'),
        ('outros', 'Outros'),  # ← NOVA OPÇÃO ADICIONADA
    ]
    
    # ===== CAMPOS DE IDENTIFICAÇÃO =====
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código")
    codigo_master = models.CharField(max_length=20, blank=True, null=True, verbose_name="Código Master",
                                    help_text="Se preenchido, indica que este é um sub-cliente")
    nome = models.CharField(max_length=100, verbose_name="Nome")
    nome_fantasia = models.CharField(max_length=200, blank=True, null=True, verbose_name="Nome Fantasia")
    
    # ===== STATUS =====
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='ativo', 
        verbose_name="Status"
    )
    
    # ===== CAMPOS DE ENDEREÇO =====
    tipo_logradouro = models.CharField(max_length=20, blank=True, null=True, verbose_name="Tipo de Logradouro",
                                     help_text="Ex: Rua, Avenida, Alameda, etc.")
    endereco = models.CharField(max_length=200, blank=True, null=True, verbose_name="Logradouro")
    numero = models.CharField(max_length=10, blank=True, null=True, verbose_name="Número")
    complemento = models.CharField(max_length=100, blank=True, null=True, verbose_name="Complemento")
    bairro = models.CharField(max_length=100, blank=True, null=True, verbose_name="Bairro")
    cidade = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade")
    estado = models.CharField(max_length=2, blank=True, null=True, verbose_name="Estado")
    cep = models.CharField(max_length=10, blank=True, null=True, verbose_name="CEP")
    
    # ===== CAMPOS DE CONTATO =====
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    
    # ===== DATAS E OBSERVAÇÕES =====
    data_cadastro = models.DateField(default=timezone.now, verbose_name="Data de Cadastro")
    data_ultima_compra = models.DateField(blank=True, null=True, verbose_name="Data da Última Compra")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    
    # ===== INFORMAÇÕES COMERCIAIS (INTEGRAÇÃO COM SYSFAT) =====
    codigo_loja = models.CharField(max_length=3, blank=True, null=True, 
                                   verbose_name="Código da Loja",
                                   help_text="Código de 3 dígitos da loja (NUMLOJ no SysFat)")
    codigo_vendedor = models.CharField(max_length=3, blank=True, null=True, 
                                      verbose_name="Código do Vendedor",
                                      help_text="Código de 3 dígitos do vendedor (CODVEN no SysFat)")
    uf = models.CharField(max_length=2, blank=True, null=True, 
                         verbose_name="UF",
                         help_text="Unidade Federativa (UF no SysFat)")
    
    # ===== DADOS FISCAIS =====
    cpf_cnpj = models.CharField(max_length=20, blank=True, null=True, verbose_name="CPF/CNPJ")
    tipo_documento = models.CharField(
        max_length=10, 
        choices=[('cpf', 'CPF'), ('cnpj', 'CNPJ')],
        default='cpf',
        blank=True, null=True,
        verbose_name="Tipo de Documento"
    )
    nome_razao_social = models.CharField(max_length=200, blank=True, null=True, verbose_name="Nome/Razão Social")
    
    # ===== DADOS DA RECEITA FEDERAL =====
    inscricao_estadual = models.CharField(max_length=30, blank=True, null=True, verbose_name="Inscrição Estadual")
    inscricao_municipal = models.CharField(max_length=30, blank=True, null=True, verbose_name="Inscrição Municipal")
    situacao_cadastral = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        choices=SITUACAO_CADASTRAL_CHOICES,
        verbose_name="Situação Cadastral"
    )
    data_situacao_cadastral = models.DateField(blank=True, null=True, verbose_name="Data da Situação Cadastral")
    motivo_situacao_cadastral = models.CharField(max_length=100, blank=True, null=True, verbose_name="Motivo da Situação Cadastral")
    data_ultima_verificacao = models.DateTimeField(blank=True, null=True, verbose_name="Data da Última Verificação")
    
    # ===== CAMPOS PARA PESSOA JURÍDICA =====
    natureza_juridica = models.CharField(max_length=100, blank=True, null=True, verbose_name="Natureza Jurídica")
    codigo_natureza_juridica = models.CharField(max_length=10, blank=True, null=True, verbose_name="Código Natureza Jurídica")
    porte_empresa = models.CharField(max_length=30, blank=True, null=True, verbose_name="Porte da Empresa")
    cnae_principal = models.CharField(max_length=20, blank=True, null=True, verbose_name="CNAE Principal")
    cnae_descricao = models.CharField(max_length=200, blank=True, null=True, verbose_name="Descrição do CNAE")
    data_abertura = models.DateField(blank=True, null=True, verbose_name="Data de Abertura")
    data_inicio_atividade = models.DateField(blank=True, null=True, verbose_name="Data de Início das Atividades")
    capital_social = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, verbose_name="Capital Social")
    
    # ===== CAMPOS PARA OPÇÕES TRIBUTÁRIAS =====
    opcao_pelo_simples = models.BooleanField(default=False, verbose_name="Optante pelo Simples")
    data_opcao_pelo_simples = models.DateField(blank=True, null=True, verbose_name="Data da Opção pelo Simples")
    data_exclusao_do_simples = models.DateField(blank=True, null=True, verbose_name="Data da Exclusão do Simples")
    opcao_pelo_mei = models.BooleanField(default=False, verbose_name="Optante pelo MEI")
    
    # ===== CAMPOS PARA CONTATO DA RECEITA =====
    ddd_telefone_1 = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone 1")
    ddd_telefone_2 = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone 2")
    ddd_fax = models.CharField(max_length=20, blank=True, null=True, verbose_name="Fax")
    email_receita = models.EmailField(blank=True, null=True, verbose_name="Email Cadastrado na Receita")

    # ===== PROPERTIES E MÉTODOS =====
    
    @property
    def nome_vendedor(self):
        """
        Property que busca o nome do vendedor automaticamente
        Usa cache para otimizar performance
        """
        if not self.codigo_vendedor:
            return ''
        
        # Normalizar código para 3 dígitos
        codigo_formatado = str(self.codigo_vendedor).zfill(3)
        
        # Chave do cache
        cache_key = f'vendedor_nome_{codigo_formatado}'
        
        # Tentar buscar no cache primeiro
        nome_cached = cache.get(cache_key)
        if nome_cached is not None:
            return nome_cached
        
        try:
            # Importar aqui para evitar importação circular
            from core.models import Vendedor
            vendedor = Vendedor.objects.select_related('loja').get(
                codigo=codigo_formatado, 
                ativo=True
            )
            nome = vendedor.nome
            
            # Cachear por 5 minutos
            cache.set(cache_key, nome, 300)
            
            return nome
            
        except Exception:  # Pode ser Vendedor.DoesNotExist ou ImportError
            # Cachear resultado negativo por 1 minuto
            cache.set(cache_key, '', 60)
            return ''
    
    @property
    def vendedor_completo(self):
        """
        Retorna objeto Vendedor completo (com dados da loja)
        Usa cache para otimizar performance
        """
        if not self.codigo_vendedor:
            return None
        
        codigo_formatado = str(self.codigo_vendedor).zfill(3)
        cache_key = f'vendedor_obj_{codigo_formatado}'
        
        # Tentar buscar no cache primeiro
        vendedor_cached = cache.get(cache_key)
        if vendedor_cached is not None:
            return vendedor_cached
        
        try:
            from core.models import Vendedor
            vendedor = Vendedor.objects.select_related('loja').get(
                codigo=codigo_formatado, 
                ativo=True
            )
            
            # Cachear por 5 minutos
            cache.set(cache_key, vendedor, 300)
            return vendedor
            
        except Exception:
            # Cachear resultado negativo por 1 minuto
            cache.set(cache_key, None, 60)
            return None
    
    @property
    def vendedor_info_completa(self):
        """
        Retorna informações completas do vendedor formatadas
        """
        if not self.codigo_vendedor:
            return "Vendedor não informado"
        
        nome = self.nome_vendedor
        if nome:
            return f"{self.codigo_vendedor} - {nome}"
        else:
            return f"{self.codigo_vendedor} - Vendedor não encontrado"
    
    @property
    def vendedor_loja_info(self):
        """
        Retorna informações do vendedor + loja
        """
        vendedor = self.vendedor_completo
        if not vendedor:
            return None
        
        info = {
            'codigo': vendedor.codigo,
            'nome': vendedor.nome,
            'email': vendedor.email or '',
            'telefone': vendedor.telefone or '',
            'loja_codigo': vendedor.loja.codigo if vendedor.loja else '',
            'loja_nome': vendedor.loja.nome if vendedor.loja else '',
            'loja_info': f"{vendedor.loja.codigo} - {vendedor.loja.nome}" if vendedor.loja else ''
        }
        return info
    
    def limpar_cache_vendedor(self):
        """
        Limpa o cache do vendedor (útil quando vendedor é alterado)
        """
        if self.codigo_vendedor:
            codigo_formatado = str(self.codigo_vendedor).zfill(3)
            cache.delete(f'vendedor_nome_{codigo_formatado}')
            cache.delete(f'vendedor_obj_{codigo_formatado}')
    
    def is_cliente_principal(self):
        """Verifica se este cliente é um cliente principal (não tem código master)"""
        return self.codigo_master is None or self.codigo_master == ""
    
    def get_sub_clientes(self):
        """Retorna todos os sub-clientes deste cliente principal"""
        if self.is_cliente_principal():
            return Cliente.objects.filter(codigo_master=self.codigo).order_by('nome')
        return Cliente.objects.none()
    
    @property
    def ativo(self):
        """Propriedade para compatibilidade - retorna True se status for 'ativo'"""
        return self.status == 'ativo'
    
    def get_situacao_cadastral_display_customizada(self):
        """
        Retorna a situação cadastral formatada corretamente
        """
        if not self.situacao_cadastral:
            return "Não informada"
            
        # Mapeamento de códigos para descrições
        mapeamento = {
            '01': 'Nula',
            '02': 'Ativa',
            '03': 'Suspensa',
            '04': 'Inapta',
            '08': 'Baixada',
            '2.0': 'Ativa',
            '3.0': 'Suspensa',
            '4.0': 'Inapta',
            '8.0': 'Baixada',
            '2': 'Ativa',
            '3': 'Suspensa',
            '4': 'Inapta',
            '8': 'Baixada',
        }
        
        return mapeamento.get(str(self.situacao_cadastral), self.situacao_cadastral)

    def save(self, *args, **kwargs):
        """
        Override save para limpar cache quando código do vendedor muda
        """
        # Se é uma instância existente, verificar se código mudou
        if self.pk:
            try:
                old_instance = Cliente.objects.get(pk=self.pk)
                if old_instance.codigo_vendedor != self.codigo_vendedor:
                    # Limpar cache do vendedor antigo
                    if old_instance.codigo_vendedor:
                        old_codigo = str(old_instance.codigo_vendedor).zfill(3)
                        cache.delete(f'vendedor_nome_{old_codigo}')
                        cache.delete(f'vendedor_obj_{old_codigo}')
                    
                    # Limpar cache do vendedor novo
                    self.limpar_cache_vendedor()
                    
                    logger.info(f"🔄 Código do vendedor alterado para cliente {self.codigo}: {old_instance.codigo_vendedor} → {self.codigo_vendedor}")
            except Cliente.DoesNotExist:
                pass
        
        # Normalizar código do vendedor
        if self.codigo_vendedor:
            self.codigo_vendedor = str(self.codigo_vendedor).zfill(3)
        
        super().save(*args, **kwargs)
    
    @classmethod 
    def limpar_cache_vendedores(cls):
        """
        Método utilitário para limpar todo o cache de vendedores
        Útil quando dados de vendedores são atualizados em lote
        """
        try:
            # Buscar todos os códigos de vendedores únicos
            codigos = cls.objects.exclude(
                codigo_vendedor__isnull=True
            ).exclude(
                codigo_vendedor=''
            ).values_list('codigo_vendedor', flat=True).distinct()
            
            for codigo in codigos:
                codigo_formatado = str(codigo).zfill(3)
                cache.delete(f'vendedor_nome_{codigo_formatado}')
                cache.delete(f'vendedor_obj_{codigo_formatado}')
            
            logger.info(f"🧹 Cache de vendedores limpo para {len(codigos)} códigos")
            return len(codigos)
            
        except Exception as e:
            logger.error(f"Erro ao limpar cache de vendedores: {str(e)}")
            return 0

    def __str__(self):
        return f"{self.codigo} - {self.nome}"
    
    class Meta:
        db_table = 'clientes'
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["nome"]


# ===== SINAIS PARA LIMPAR CACHE QUANDO VENDEDOR É ALTERADO =====
# (Devem ficar FORA da classe, no final do arquivo)

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver([post_save, post_delete], sender='core.Vendedor')
def limpar_cache_vendedor_alterado(sender, instance, **kwargs):
    """
    Limpa o cache quando um vendedor é alterado ou deletado
    """
    codigo_formatado = str(instance.codigo).zfill(3)
    cache.delete(f'vendedor_nome_{codigo_formatado}')
    cache.delete(f'vendedor_obj_{codigo_formatado}')
    logger.info(f"🧹 Cache limpo para vendedor {codigo_formatado} - {instance.nome}")

# ===== OUTROS MODELOS =====
class ClienteContato(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='contatos', verbose_name="Cliente")
    codigo = models.CharField(max_length=20, verbose_name="Código")
    codigo_master = models.CharField(max_length=20, blank=True, null=True, verbose_name="Código Master")
    whatsapp = models.CharField(max_length=20, verbose_name="WhatsApp")
    nome = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nome do Contato")
    cargo = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cargo")
    principal = models.BooleanField(default=False, verbose_name="Contato Principal")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    # Campos para integração com ChatWoot
    chatwoot_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="ID no ChatWoot")
    chatwoot_inbox_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="ID da Caixa de Entrada no ChatWoot")
    ultima_sincronizacao = models.DateField(blank=True, null=True, verbose_name="Última Sincronização")
    
    def save(self, *args, **kwargs):
        # Se estamos criando um novo objeto (não tem ID ainda)
        if not self.id:
            # Se o código_master não foi informado, usar o código do cliente
            if not self.codigo_master:
                self.codigo_master = self.cliente.codigo
                
        # Se este contato está marcado como principal, atualizar os outros contatos
        if self.principal:
            # Desmarcar outros contatos principais do mesmo cliente
            ClienteContato.objects.filter(cliente=self.cliente, principal=True).exclude(pk=self.pk if self.pk else None).update(principal=False)
            
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.nome or 'Sem nome'} - {self.whatsapp}"
    
    class Meta:
        db_table = 'cliente_contatos'
        verbose_name = "Contato do Cliente"
        verbose_name_plural = "Contatos dos Clientes"
        ordering = ["-principal", "nome"]

# ===== MODELO CNAE SECUNDÁRIO =====

class ClienteCnaeSecundario(models.Model):
    """
    Modelo para armazenar CNAEs secundários dos clientes da Receita Federal
    """
    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.CASCADE, 
        related_name='cnaes_secundarios', 
        verbose_name="Cliente"
    )
    codigo_cnae = models.CharField(
        max_length=10, 
        verbose_name="Código CNAE",
        help_text="Código CNAE da Receita Federal (ex: 4761003)"
    )
    descricao_cnae = models.CharField(
        max_length=200, 
        verbose_name="Descrição do CNAE",
        help_text="Descrição oficial da atividade econômica"
    )
    ordem = models.PositiveSmallIntegerField(
        default=1, 
        verbose_name="Ordem", 
        help_text="Ordem do CNAE secundário (1, 2, 3...)"
    )
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação"
    )
    
    class Meta:
        db_table = 'cliente_cnaes_secundarios'
        verbose_name = "CNAE Secundário do Cliente"
        verbose_name_plural = "CNAEs Secundários dos Clientes"
        ordering = ['cliente', 'ordem']
        constraints = [
            models.UniqueConstraint(
                fields=['cliente', 'codigo_cnae'], 
                name='unique_cliente_cnae'
            )
        ]
        indexes = [
            models.Index(fields=['cliente', 'ordem'], name='idx_cliente_cnae_ordem'),
            models.Index(fields=['codigo_cnae'], name='idx_cnae_codigo'),
        ]
    
    def __str__(self):
        return f"{self.cliente.codigo} - {self.codigo_cnae}: {self.descricao_cnae[:50]}"
    
    def clean(self):
        """Validação personalizada"""
        from django.core.exceptions import ValidationError
        
        # Validar formato do CNAE (deve ser numérico)
        if not self.codigo_cnae.isdigit():
            raise ValidationError({
                'codigo_cnae': 'Código CNAE deve conter apenas números'
            })
    
    def save(self, *args, **kwargs):
        """Override save para limpeza automática"""
        self.full_clean()  # Chama clean() automaticamente
        super().save(*args, **kwargs)

# Modelo para registrar sincronizações com sistemas externos
class LogSincronizacao(models.Model):
    TIPO_CHOICES = [
        ('bi', 'BI SysFat'),
        ('receita', 'Receita Federal'),
        ('chatwoot', 'ChatWoot'),
    ]
    
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    data_inicio = models.DateTimeField(auto_now_add=True)
    data_termino = models.DateTimeField(blank=True, null=True)
    registros_processados = models.IntegerField(default=0)
    registros_criados = models.IntegerField(default=0)
    registros_atualizados = models.IntegerField(default=0)
    registros_com_erro = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default='iniciado')
    mensagem = models.TextField(blank=True, null=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.data_inicio}"
    
    class Meta:
        db_table = 'log_sincronizacao'
        verbose_name = "Log de Sincronização"
        verbose_name_plural = "Logs de Sincronização"
        ordering = ["-data_inicio"]


# ===== MODELO VENDAS ATUALIZADO =====
class Vendas(models.Model):
    # ===== RELACIONAMENTOS =====
    loja = models.ForeignKey(Loja, on_delete=models.PROTECT, verbose_name="Loja")
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT, verbose_name="Produto")
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='vendas', verbose_name="Cliente")
    grupo_produto = models.ForeignKey(GrupoProduto, on_delete=models.PROTECT, related_name='vendas', verbose_name="Grupo de Produto")
    fabricante = models.ForeignKey(Fabricante, on_delete=models.PROTECT, related_name='vendas', verbose_name="Fabricante")
    
    # ===== VENDEDOR HISTÓRICO (ÚNICO CAMPO) =====
    # ❌ REMOVIDO: vendedor = models.ForeignKey(Vendedor, on_delete=models.PROTECT, verbose_name="Vendedor")
    vendedor_nf = models.CharField(
        max_length=3, 
        blank=True, 
        null=True, 
        verbose_name="Vendedor da NF",
        help_text="Código do vendedor que fez a venda (histórico da NF)"
    )
    
    # ===== DADOS DA VENDA =====
    data_venda = models.DateField(verbose_name="Data da Venda")
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Quantidade")
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Total")
    
    # ===== DADOS DA NOTA FISCAL =====
    numero_nf = models.CharField(max_length=20, blank=True, null=True, verbose_name="Número NF")
    serie_nf = models.CharField(max_length=3, blank=True, null=True, verbose_name="Série NF")
    estado = models.CharField(max_length=2, blank=True, null=True, verbose_name="Estado")
    
    # ===== CAMPOS CALCULADOS PARA RELATÓRIOS =====
    anomes = models.CharField(max_length=6, verbose_name="Ano/Mês", db_index=True,
                             help_text="Formato: YYYYMM")
    ano = models.CharField(max_length=4, verbose_name="Ano", db_index=True)
    mes = models.CharField(max_length=2, verbose_name="Mês", db_index=True)
    
    # ===== METADADOS =====
    data_importacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Importação")
    origem_sistema = models.CharField(max_length=20, default="BI", verbose_name="Sistema de Origem")
    
    # ===== PROPERTIES PARA VENDEDOR HISTÓRICO (NF) =====
    
    @property
    def vendedor_nf_nome(self):
        """Nome do vendedor que fez a venda (histórico da NF)"""
        if not self.vendedor_nf:
            return ''
        
        codigo_formatado = str(self.vendedor_nf).zfill(3)
        cache_key = f'vendedor_nome_{codigo_formatado}'
        
        nome_cached = cache.get(cache_key)
        if nome_cached is not None:
            return nome_cached
        
        try:
            vendedor = Vendedor.objects.get(codigo=codigo_formatado, ativo=True)
            nome = vendedor.nome
            cache.set(cache_key, nome, 300)
            return nome
        except Vendedor.DoesNotExist:
            cache.set(cache_key, '', 60)
            return ''
    
    @property
    def vendedor_nf_obj(self):
        """Objeto Vendedor que fez a venda (histórico)"""
        if not self.vendedor_nf:
            return None
        
        codigo_formatado = str(self.vendedor_nf).zfill(3)
        cache_key = f'vendedor_obj_{codigo_formatado}'
        
        vendedor_cached = cache.get(cache_key)
        if vendedor_cached is not None:
            return vendedor_cached
        
        try:
            vendedor = Vendedor.objects.select_related('loja').get(
                codigo=codigo_formatado, ativo=True
            )
            cache.set(cache_key, vendedor, 300)
            return vendedor
        except Vendedor.DoesNotExist:
            cache.set(cache_key, None, 60)
            return None
    
    # ===== PROPERTIES PARA VENDEDOR ATUAL DO CLIENTE =====
    
    @property
    def vendedor_atual_cliente(self):
        """Vendedor ATUAL do cliente (não o da NF)"""
        return self.cliente.vendedor_atual if self.cliente else None
    
    @property
    def codigo_vendedor_atual_cliente(self):
        """Código do vendedor ATUAL do cliente"""
        return self.cliente.codigo_vendedor if self.cliente else ''
    
    @property
    def nome_vendedor_atual_cliente(self):
        """Nome do vendedor ATUAL do cliente"""
        return self.cliente.nome_vendedor if self.cliente else ''
    
    @property
    def vendedor_mudou(self):
        """Verifica se o vendedor do cliente mudou desde a venda"""
        if not self.vendedor_nf or not self.cliente.codigo_vendedor:
            return False
        return str(self.vendedor_nf).zfill(3) != str(self.cliente.codigo_vendedor).zfill(3)
    
    # ===== PROPERTIES PARA COMPATIBILIDADE (se necessário) =====
    
    @property
    def vendedor(self):
        """Property para compatibilidade - retorna objeto vendedor da NF"""
        return self.vendedor_nf_obj
    
    @property
    def codigo_vendedor(self):
        """Property para compatibilidade - retorna código do vendedor da NF"""
        return self.vendedor_nf
    
    @property
    def nome_vendedor(self):
        """Property para compatibilidade - retorna nome do vendedor da NF"""
        return self.vendedor_nf_nome
    
    def save(self, *args, **kwargs):
        # Calcular campos derivados automaticamente
        if self.data_venda:
            self.ano = str(self.data_venda.year)
            self.mes = str(self.data_venda.month).zfill(2)
            self.anomes = f"{self.ano}{self.mes}"
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Venda {self.numero_nf or 'S/N'} - {self.data_venda} - {self.cliente.nome}"
    
    class Meta:
        db_table = 'vendas'
        verbose_name = "Venda"
        verbose_name_plural = "Vendas"
        ordering = ["-data_venda"]
        indexes = [
            models.Index(fields=['loja', 'cliente']),
            models.Index(fields=['vendedor_nf']),  # Index para vendedor histórico
            models.Index(fields=['cliente', 'data_venda']),
            models.Index(fields=['data_venda']),
            models.Index(fields=['anomes']),
            models.Index(fields=['ano', 'mes']),
        ]
