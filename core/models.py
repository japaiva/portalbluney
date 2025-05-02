# django/afinal/core/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings

class Usuario(AbstractUser):
    NIVEL_CHOICES = [
        ('admin', 'Admin'),
        ('gestor', 'Gestor'),
        ('projetista', 'Projetista'),
        ('cliente', 'Cliente'),
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
            ('cliente', 'Cliente')
        ],
        default='cliente'
    )
    
    def __str__(self):
        return f"{self.usuario.username} - {self.get_nivel_display()}"

class Cliente(models.Model):
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código")
    nome = models.CharField(max_length=100, verbose_name="Nome")
    endereco = models.CharField(max_length=200, blank=True, null=True, verbose_name="Endereço")
    cidade = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade")
    estado = models.CharField(max_length=2, blank=True, null=True, verbose_name="Estado")
    cep = models.CharField(max_length=10, blank=True, null=True, verbose_name="CEP")
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"
    
    class Meta:
        db_table = 'clientes'
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["nome"]

class Contato(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='contatos', verbose_name="Cliente")
    whatsapp = models.CharField(max_length=20, verbose_name="WhatsApp")
    nome = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nome do Contato")
    cargo = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cargo")
    principal = models.BooleanField(default=False, verbose_name="Contato Principal")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    def __str__(self):
        return f"{self.nome or 'Sem nome'} - {self.whatsapp}"
    
    class Meta:
        db_table = 'contatos'
        verbose_name = "Contato"
        verbose_name_plural = "Contatos"
        ordering = ["-principal", "nome"]

class ClienteItem(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='itens', verbose_name="Cliente")
    cpf_cnpj = models.CharField(max_length=20, verbose_name="CPF/CNPJ")
    nome_razao = models.CharField(max_length=200, blank=True, null=True, verbose_name="Nome/Razão Social")
    tipo = models.CharField(
        max_length=10, 
        choices=[('cpf', 'CPF'), ('cnpj', 'CNPJ')],
        default='cpf',
        verbose_name="Tipo"
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    def __str__(self):
        return f"{self.cpf_cnpj} - {self.nome_razao or 'Sem nome'}"
    
    class Meta:
        db_table = 'cliente_itens'
        verbose_name = "Item do Cliente"
        verbose_name_plural = "Itens dos Clientes"
        ordering = ["cpf_cnpj"]