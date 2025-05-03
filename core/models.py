# core/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings

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

# Modelos de Cadastro Básico
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

class ClasseProduto(models.Model):
    codigo = models.CharField(max_length=4, primary_key=True)
    descricao = models.CharField(max_length=100)
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.codigo} - {self.descricao}"
    
    class Meta:
        db_table = 'classes_produto'
        verbose_name = 'Classe de Produto'
        verbose_name_plural = 'Classes de Produto'
        ordering = ['codigo']

class Produto(models.Model):
    codigo = models.CharField(max_length=6, primary_key=True)
    descricao = models.CharField(max_length=200)
    classe = models.ForeignKey(ClasseProduto, on_delete=models.PROTECT, related_name='produtos')
    preco = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.codigo} - {self.descricao}"
    
    class Meta:
        db_table = 'produtos'
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['codigo']


from django.db import models
from django.utils import timezone

class Cliente(models.Model):
    # Campos de identificação
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código")
    codigo_master = models.CharField(max_length=20, blank=True, null=True, verbose_name="Código Master",
                                    help_text="Se preenchido, indica que este é um sub-cliente")
    nome = models.CharField(max_length=100, verbose_name="Nome")
    nome_fantasia = models.CharField(max_length=200, blank=True, null=True, verbose_name="Nome Fantasia")
    
    # Campos de endereço
    tipo_logradouro = models.CharField(max_length=20, blank=True, null=True, verbose_name="Tipo de Logradouro",
                                     help_text="Ex: Rua, Avenida, Alameda, etc.")
    endereco = models.CharField(max_length=200, blank=True, null=True, verbose_name="Logradouro")
    numero = models.CharField(max_length=10, blank=True, null=True, verbose_name="Número")
    complemento = models.CharField(max_length=100, blank=True, null=True, verbose_name="Complemento")
    bairro = models.CharField(max_length=100, blank=True, null=True, verbose_name="Bairro")
    cidade = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade")
    estado = models.CharField(max_length=2, blank=True, null=True, verbose_name="Estado")
    cep = models.CharField(max_length=10, blank=True, null=True, verbose_name="CEP")
    
    # Campos de contato
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    
    # Status e datas
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(default=timezone.now, verbose_name="Data de Cadastro")
    data_ultima_compra = models.DateField(blank=True, null=True, verbose_name="Data da Última Compra")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    
    # Campos para integração com SysFat 
    codigo_loja = models.CharField(max_length=3, blank=True, null=True, 
                                   verbose_name="Código da Loja",
                                   help_text="Código de 3 dígitos da loja (NUMLOJ no SysFat)")
    codigo_vendedor = models.CharField(max_length=3, blank=True, null=True, 
                                      verbose_name="Código do Vendedor",
                                      help_text="Código de 3 dígitos do vendedor (CODVEN no SysFat)")
    nome_vendedor = models.CharField(max_length=100, blank=True, null=True, 
                                    verbose_name="Nome do Vendedor",
                                    help_text="Nome do vendedor (VEND no SysFat)")
    uf = models.CharField(max_length=2, blank=True, null=True, 
                         verbose_name="UF",
                         help_text="Unidade Federativa (UF no SysFat)")
    
    # Dados fiscais
    cpf_cnpj = models.CharField(max_length=20, blank=True, null=True, verbose_name="CPF/CNPJ")
    tipo_documento = models.CharField(
        max_length=10, 
        choices=[('cpf', 'CPF'), ('cnpj', 'CNPJ')],
        default='cpf',
        blank=True, null=True,
        verbose_name="Tipo de Documento"
    )
    nome_razao_social = models.CharField(max_length=200, blank=True, null=True, verbose_name="Nome/Razão Social")
    
    # Dados da Receita Federal
    inscricao_estadual = models.CharField(max_length=30, blank=True, null=True, verbose_name="Inscrição Estadual")
    inscricao_municipal = models.CharField(max_length=30, blank=True, null=True, verbose_name="Inscrição Municipal")
    situacao_cadastral = models.CharField(max_length=50, blank=True, null=True, verbose_name="Situação Cadastral")
    data_situacao_cadastral = models.DateField(blank=True, null=True, verbose_name="Data da Situação Cadastral")
    motivo_situacao_cadastral = models.CharField(max_length=100, blank=True, null=True, verbose_name="Motivo da Situação Cadastral")
    data_ultima_verificacao = models.DateTimeField(blank=True, null=True, verbose_name="Data da Última Verificação")
    
    # Campos para pessoa jurídica
    natureza_juridica = models.CharField(max_length=100, blank=True, null=True, verbose_name="Natureza Jurídica")
    codigo_natureza_juridica = models.CharField(max_length=10, blank=True, null=True, verbose_name="Código Natureza Jurídica")
    porte_empresa = models.CharField(max_length=30, blank=True, null=True, verbose_name="Porte da Empresa")
    cnae_principal = models.CharField(max_length=20, blank=True, null=True, verbose_name="CNAE Principal")
    cnae_descricao = models.CharField(max_length=200, blank=True, null=True, verbose_name="Descrição do CNAE")
    data_abertura = models.DateField(blank=True, null=True, verbose_name="Data de Abertura")
    data_inicio_atividade = models.DateField(blank=True, null=True, verbose_name="Data de Início das Atividades")
    capital_social = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, verbose_name="Capital Social")
    
    # Campos para opções tributárias
    opcao_pelo_simples = models.BooleanField(default=False, verbose_name="Optante pelo Simples")
    data_opcao_pelo_simples = models.DateField(blank=True, null=True, verbose_name="Data da Opção pelo Simples")
    data_exclusao_do_simples = models.DateField(blank=True, null=True, verbose_name="Data da Exclusão do Simples")
    opcao_pelo_mei = models.BooleanField(default=False, verbose_name="Optante pelo MEI")
    
    # Campos para contato da Receita
    ddd_telefone_1 = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone 1")
    ddd_telefone_2 = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone 2")
    ddd_fax = models.CharField(max_length=20, blank=True, null=True, verbose_name="Fax")
    email_receita = models.EmailField(blank=True, null=True, verbose_name="Email Cadastrado na Receita")
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"
    
    class Meta:
        db_table = 'clientes'
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["nome"]
        
    def is_cliente_principal(self):
        """Verifica se este cliente é um cliente principal (não tem código master)"""
        return self.codigo_master is None or self.codigo_master == ""
    
    def get_sub_clientes(self):
        """Retorna todos os sub-clientes deste cliente principal"""
        if self.is_cliente_principal():
            return Cliente.objects.filter(codigo_master=self.codigo).order_by('nome')
        return Cliente.objects.none()


# Modelo ClienteContato atualizado
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
    ultima_sincronizacao = models.DateTimeField(blank=True, null=True, verbose_name="Última Sincronização")
    
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

# RegistroBI (para armazenar dados do BI)
class RegistroBI(models.Model):
    # Campos de relacionamento
    loja = models.ForeignKey(Loja, on_delete=models.PROTECT, verbose_name="Loja")
    vendedor = models.ForeignKey(Vendedor, on_delete=models.PROTECT, verbose_name="Vendedor")
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT, verbose_name="Produto")
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='registros_bi', verbose_name="Cliente")
    classe_produto = models.ForeignKey(ClasseProduto, on_delete=models.PROTECT, related_name='registros_bi', verbose_name="Classe de Produto")
    
    # Dados da nota fiscal
    data_venda = models.DateField(verbose_name="Data da Venda")
    anomes = models.CharField(max_length=4, verbose_name="Ano/Mês", db_index=True,
                             help_text="Formato: AAMM (Ano e Mês)")
    ano = models.CharField(max_length=2, verbose_name="Ano", db_index=True)
    mes = models.CharField(max_length=2, verbose_name="Mês", db_index=True)
    
    # Valores
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Quantidade")
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Total")
    
    # Referências ao Clipper
    numero_nf = models.CharField(max_length=20, blank=True, null=True, verbose_name="Número NF")
    serie_nf = models.CharField(max_length=3, blank=True, null=True, verbose_name="Série NF")
    origem_sistema = models.CharField(max_length=20, default="Clipper", verbose_name="Sistema de Origem")
    
    # Metadados
    data_sincronizacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Sincronização")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    class Meta:
        db_table = 'registros_bi'
        verbose_name = "Registro de BI"
        verbose_name_plural = "Registros de BI"
        ordering = ["-data_venda"]
        indexes = [
            models.Index(fields=['loja', 'vendedor', 'produto']),
            models.Index(fields=['cliente']),
            models.Index(fields=['data_venda']),
            models.Index(fields=['anomes']),
            models.Index(fields=['ano', 'mes']),
        ]
    
    def __str__(self):
        return f"Venda {self.numero_nf} - {self.data_venda} - {self.cliente.nome}"

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