# core/forms.py
from django import forms
from django.forms import inlineformset_factory
from core.models import (Cliente, ClienteContato, ClienteCnaeSecundario, Usuario, 
                        Loja, Vendedor, Produto, GrupoProduto, Fabricante, Vendas, LogSincronizacao)
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from core.utils.view_utils import CustomDateInput, CustomDateTimeInput
from datetime import datetime
import calendar

# SUBSTITUIR o UsuarioForm em core/forms.py

from core.models import Usuario, UsuarioVendedores, Vendedor
from django.contrib.auth.hashers import make_password

class UsuarioForm(forms.ModelForm):
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}), 
        required=False,
        label="Confirmar Senha"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}), 
        required=False,
        label="Senha"
    )
    
    # CAMPO DE VENDEDORES
    vendedores_permitidos = forms.ModelMultipleChoiceField(
        queryset=Vendedor.objects.filter(ativo=True).order_by('codigo'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Vendedores Permitidos",
        help_text="Selecione os vendedores que este usuário poderá visualizar. Admin/Gestor têm acesso automático a todos."
    )
    
    class Meta:
        model = Usuario
        fields = [
            'username', 'first_name', 'last_name', 'email', 'nivel', 'telefone', 
            'codigo_loja', 'codigo_vendedor', 'is_active'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'nivel': forms.Select(attrs={'class': 'form-select'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_loja': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '3'}),
            'codigo_vendedor': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '3'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Se estiver editando um usuário existente, não exigir senha
        if self.instance.pk:
            self.fields['password'].required = False
            self.fields['confirm_password'].required = False
            
            # ✅ CARREGAR VENDEDORES ATUAIS CORRETAMENTE
            try:
                vendedores_atuais = self.instance.get_vendedores_permitidos()
                # Se não é admin/gestor, carregar só os permitidos
                if self.instance.nivel not in ['admin', 'gestor']:
                    vendedores_ids = list(UsuarioVendedores.objects.filter(
                        usuario=self.instance,
                        ativo=True
                    ).values_list('vendedor_id', flat=True))
                    self.fields['vendedores_permitidos'].initial = vendedores_ids
                else:
                    # Admin/Gestor não tem vendedores específicos
                    self.fields['vendedores_permitidos'].initial = []
            except Exception as e:
                print(f"Erro ao carregar vendedores: {e}")
                self.fields['vendedores_permitidos'].initial = []
        else:
            self.fields['password'].required = True
            self.fields['confirm_password'].required = True
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "As senhas não coincidem.")
        
        # Validação para códigos de loja e vendedor
        codigo_loja = cleaned_data.get('codigo_loja')
        if codigo_loja and (len(codigo_loja) != 3 or not codigo_loja.isdigit()):
            self.add_error('codigo_loja', "O código da loja deve ter exatamente 3 dígitos numéricos.")
        
        codigo_vendedor = cleaned_data.get('codigo_vendedor')
        if codigo_vendedor and (len(codigo_vendedor) != 3 or not codigo_vendedor.isdigit()):
            self.add_error('codigo_vendedor', "O código do vendedor deve ter exatamente 3 dígitos numéricos.")
        
        return cleaned_data
    
    def save(self, commit=True):
        usuario = super().save(commit=False)
        
        # Se uma senha foi fornecida, codificá-la
        password = self.cleaned_data.get('password')
        if password:
            usuario.password = make_password(password)
        
        if commit:
            usuario.save()
            
            # ✅ GERENCIAR VENDEDORES PERMITIDOS CORRETAMENTE
            vendedores_selecionados = self.cleaned_data.get('vendedores_permitidos', [])
            
            # Se é admin ou gestor, não criar associações
            if usuario.nivel in ['admin', 'gestor']:
                # Limpar associações se existirem
                UsuarioVendedores.objects.filter(usuario=usuario).delete()
                print(f"✅ Admin/Gestor {usuario.username}: associações removidas")
            else:
                # Limpar associações antigas
                UsuarioVendedores.objects.filter(usuario=usuario).delete()
                
                # Criar novas associações
                for vendedor in vendedores_selecionados:
                    UsuarioVendedores.objects.create(
                        usuario=usuario,
                        vendedor=vendedor,
                        ativo=True
                    )
                    print(f"✅ Vendedor {vendedor.codigo} associado ao usuário {usuario.username}")
                
                print(f"✅ Total de {len(vendedores_selecionados)} vendedores associados")
        
        return usuario
class ClienteForm(forms.ModelForm):
    # *** CAMPO VIRTUAL PARA EXIBIR O NOME DO VENDEDOR ***
    nome_vendedor_display = forms.CharField(
        label="Nome do Vendedor",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': True,
            'placeholder': 'Preenchido automaticamente'
        })
    )
    
    class Meta:
        model = Cliente
        fields = [
            # ===== INFORMAÇÕES PRINCIPAIS =====
            'codigo', 'codigo_master', 'nome', 'nome_fantasia', 'status',
            
            # ===== INFORMAÇÕES COMERCIAIS =====
            'codigo_loja', 'codigo_vendedor',  # *** REMOVIDO nome_vendedor ***
            'data_cadastro', 'data_ultima_compra',
            
            # ===== DADOS FISCAIS =====
            'tipo_documento', 'cpf_cnpj', 'nome_razao_social',
            'inscricao_estadual', 'inscricao_municipal', 'situacao_cadastral',
            
            # ===== ENDEREÇO COMPLETO =====
            'tipo_logradouro', 'endereco', 'numero', 'complemento', 
            'bairro', 'cidade', 'estado', 'cep',
            
            # ===== RECEITA FEDERAL =====
            'cnae_principal', 'cnae_descricao', 'porte_empresa',
            'natureza_juridica', 'data_abertura', 'data_ultima_verificacao',
            'opcao_pelo_simples', 'opcao_pelo_mei',
            
            # ===== CONTATO =====
            'telefone', 'email', 'observacoes'
        ]
        
        widgets = {
            # ===== INFORMAÇÕES PRINCIPAIS =====
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_master': forms.TextInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'nome_fantasia': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            
            # ===== INFORMAÇÕES COMERCIAIS =====
            'codigo_loja': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '3'}),
            'codigo_vendedor': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '3'}),
            'data_cadastro': CustomDateInput(attrs={'class': 'form-control'}),
            'data_ultima_compra': CustomDateInput(attrs={'class': 'form-control'}),
            
            # ===== DADOS FISCAIS =====
            'tipo_documento': forms.Select(attrs={'class': 'form-select'}),
            'cpf_cnpj': forms.TextInput(attrs={'class': 'form-control'}),
            'nome_razao_social': forms.TextInput(attrs={'class': 'form-control'}),
            'inscricao_estadual': forms.TextInput(attrs={'class': 'form-control'}),
            'inscricao_municipal': forms.TextInput(attrs={'class': 'form-control'}),
            'situacao_cadastral': forms.Select(attrs={'class': 'form-select'}),
            
            # ===== ENDEREÇO =====
            'tipo_logradouro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Rua, Avenida, etc.'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'complemento': forms.TextInput(attrs={'class': 'form-control'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-select'}, 
                               choices=[('', '---')] + [(s, s) for s in [
                                   'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 
                                   'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 
                                   'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
                               ]]),
            'cep': forms.TextInput(attrs={'class': 'form-control', 'data-mask': '00000-000'}),
            
            # ===== RECEITA FEDERAL =====
            'cnae_principal': forms.TextInput(attrs={'class': 'form-control'}),
            'cnae_descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'porte_empresa': forms.TextInput(attrs={'class': 'form-control'}),
            'natureza_juridica': forms.TextInput(attrs={'class': 'form-control'}),
            'data_abertura': CustomDateInput(attrs={'class': 'form-control'}),
            'data_ultima_verificacao': CustomDateInput(attrs={'class': 'form-control'}),
            'opcao_pelo_simples': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'opcao_pelo_mei': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
            # ===== CONTATO =====
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'data-mask': '(00) 00000-0000'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super(ClienteForm, self).__init__(*args, **kwargs)
        
        # Tornar alguns campos obrigatórios
        self.fields['codigo'].required = True
        self.fields['nome'].required = True
        
        # Configurar choices para situação cadastral
        self.fields['situacao_cadastral'].choices = [('', '---')] + Cliente.SITUACAO_CADASTRAL_CHOICES
        
        # *** PREENCHER CAMPO VIRTUAL COM NOME DO VENDEDOR ***
        if self.instance and self.instance.pk:
            # Para instância existente, usar a property
            self.fields['nome_vendedor_display'].initial = self.instance.nome_vendedor
        elif self.data and self.data.get('codigo_vendedor'):
            # Para formulário sendo submetido, buscar o nome
            codigo_vendedor = self.data.get('codigo_vendedor')
            if codigo_vendedor and len(codigo_vendedor) == 3:
                try:
                    vendedor = Vendedor.objects.get(codigo=codigo_vendedor, ativo=True)
                    self.fields['nome_vendedor_display'].initial = vendedor.nome
                except Vendedor.DoesNotExist:
                    self.fields['nome_vendedor_display'].initial = ''
        
        # Se for uma nova instância, preencher data de cadastro
        if not self.instance.pk and not self.data.get('data_cadastro'):
            self.initial['data_cadastro'] = timezone.now().strftime('%Y-%m-%d')
    
    def clean_codigo_vendedor(self):
        """Validação específica para código do vendedor"""
        codigo_vendedor = self.cleaned_data.get('codigo_vendedor')
        if codigo_vendedor:
            # Normalizar para 3 dígitos
            codigo_vendedor = str(codigo_vendedor).zfill(3)
            
            # Validar formato
            if len(codigo_vendedor) != 3 or not codigo_vendedor.isdigit():
                raise forms.ValidationError("O código do vendedor deve ter exatamente 3 dígitos numéricos.")
            
            # Verificar se vendedor existe
            if not Vendedor.objects.filter(codigo=codigo_vendedor, ativo=True).exists():
                raise forms.ValidationError(f"Vendedor com código {codigo_vendedor} não encontrado ou inativo.")
            
            return codigo_vendedor
        return codigo_vendedor
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validação para códigos de loja e vendedor
        codigo_loja = cleaned_data.get('codigo_loja')
        if codigo_loja and (len(codigo_loja) != 3 or not codigo_loja.isdigit()):
            self.add_error('codigo_loja', "O código da loja deve ter exatamente 3 dígitos numéricos.")
        
        # Validação de CPF/CNPJ
        cpf_cnpj = cleaned_data.get('cpf_cnpj')
        tipo_documento = cleaned_data.get('tipo_documento')
        
        if cpf_cnpj and tipo_documento:
            # Remove caracteres não numéricos
            cpf_cnpj_numerico = ''.join(filter(str.isdigit, cpf_cnpj))
            
            if tipo_documento == 'cpf' and len(cpf_cnpj_numerico) != 11:
                self.add_error('cpf_cnpj', "CPF deve ter 11 dígitos numéricos.")
            elif tipo_documento == 'cnpj' and len(cpf_cnpj_numerico) != 14:
                self.add_error('cpf_cnpj', "CNPJ deve ter 14 dígitos numéricos.")
        
        # Validação do código master
        codigo_master = cleaned_data.get('codigo_master')
        if codigo_master:
            existe = Cliente.objects.filter(codigo=codigo_master).exists()
            if not existe:
                self.add_error('codigo_master', "Código master não existe no cadastro de clientes.")
        
        return cleaned_data
    
    def clean_situacao_cadastral(self):
        """Normaliza a situação cadastral para formato consistente"""
        situacao = self.cleaned_data.get('situacao_cadastral')
        
        if not situacao:
            return situacao
            
        # Normalizar códigos decimais para formato padrão
        normalizacao = {
            '2.0': '02',
            '3.0': '03', 
            '4.0': '04',
            '8.0': '08',
            '2': '02',
            '3': '03',
            '4': '04', 
            '8': '08',
        }
        
        return normalizacao.get(situacao, situacao)

# ===== FORM PARA CNAE SECUNDÁRIO =====

# Adicionar ao final do arquivo core/forms.py

from django.forms import inlineformset_factory
from core.models import ClienteCnaeSecundario

# Classe de Form personalizada para CNAE Secundário
class ClienteCnaeSecundarioForm(forms.ModelForm):
    class Meta:
        model = ClienteCnaeSecundario
        fields = ['codigo_cnae', 'descricao_cnae', 'ordem']
        widgets = {
            'codigo_cnae': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Ex: 4761003',
                'maxlength': 10
            }),
            'descricao_cnae': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Descrição da atividade econômica'
            }),
            'ordem': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'min': 1,
                'max': 99,
                'style': 'width: 80px;'
            }),
        }
    
    def clean_codigo_cnae(self):
        codigo = self.cleaned_data.get('codigo_cnae')
        if codigo and not codigo.isdigit():
            raise forms.ValidationError("Código CNAE deve conter apenas números")
        return codigo

# FormSet para CNAEs Secundários
ClienteCnaeSecundarioFormSet = inlineformset_factory(
    Cliente,
    ClienteCnaeSecundario,
    form=ClienteCnaeSecundarioForm,
    fields=['codigo_cnae', 'descricao_cnae', 'ordem'],
    extra=3,  # 3 campos extras vazios
    can_delete=True,
    can_order=False
)
class ClienteContatoForm(forms.ModelForm):
    class Meta:
        model = ClienteContato
        fields = ['codigo', 'codigo_master', 'nome', 'whatsapp', 'cargo', 'principal', 'ativo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_master': forms.TextInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'whatsapp': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(11) 98765-4321'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),
            'principal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_whatsapp(self):
        whatsapp = self.cleaned_data['whatsapp']
        # Remove caracteres não numéricos
        return ''.join(filter(str.isdigit, whatsapp))

class LojaForm(forms.ModelForm):
    class Meta:
        model = Loja
        fields = ['codigo', 'nome', 'endereco', 'cidade', 'estado', 'cep', 'telefone', 'email', 'ativo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '3'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-select'}, choices=[('', '---')] + [(s, s) for s in ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']]),
            'cep': forms.TextInput(attrs={'class': 'form-control', 'data-mask': '00000-000'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'data-mask': '(00) 00000-0000'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_codigo(self):
        codigo = self.cleaned_data['codigo']
        if len(codigo) != 3 or not codigo.isdigit():
            raise forms.ValidationError("O código da loja deve ter exatamente 3 dígitos numéricos.")
        return codigo

class VendedorForm(forms.ModelForm):
    class Meta:
        model = Vendedor
        fields = ['codigo', 'nome', 'email', 'telefone', 'loja', 'ativo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '3'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'data-mask': '(00) 00000-0000'}),
            'loja': forms.Select(attrs={'class': 'form-select'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_codigo(self):
        codigo = self.cleaned_data['codigo']
        if len(codigo) != 3 or not codigo.isdigit():
            raise forms.ValidationError("O código do vendedor deve ter exatamente 3 dígitos numéricos.")
        return codigo

class GrupoProdutoForm(forms.ModelForm):
    class Meta:
        model = GrupoProduto
        fields = ['codigo', 'descricao', 'ativo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '4'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_codigo(self):
        codigo = self.cleaned_data['codigo']
        if len(codigo) != 4 or not codigo.isdigit():
            raise forms.ValidationError("O código do grupo de produto deve ter exatamente 4 dígitos numéricos.")
        return codigo

class FabricanteForm(forms.ModelForm):
    class Meta:
        model = Fabricante
        fields = ['codigo', 'descricao', 'ativo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '10'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['codigo', 'descricao', 'grupo', 'fabricante', 'ativo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '6'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'grupo': forms.Select(attrs={'class': 'form-select'}),
            'fabricante': forms.Select(attrs={'class': 'form-select'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_codigo(self):
        codigo = self.cleaned_data['codigo']
        if len(codigo) != 6 or not codigo.isdigit():
            raise forms.ValidationError("O código do produto deve ter exatamente 6 dígitos numéricos.")
        return codigo


# Adicione este formulário SUBSTITUINDO o ImportarVendasForm existente no seu forms.py

class ImportarVendasForm(forms.Form):
    arquivo_csv = forms.FileField(
        label="Arquivo CSV/Excel do BI",
        help_text="Selecione o arquivo CSV ou Excel com os dados de vendas para importação",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv,.xlsx,.xls'})
    )
    
    # ===== FILTROS DE DATA =====
    data_inicio = forms.DateField(
        label="Data de Início",
        required=False,
        help_text="Se preenchida, importará apenas vendas a partir desta data",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    data_fim = forms.DateField(
        label="Data de Fim",
        required=False,
        help_text="Se preenchida, importará apenas vendas até esta data",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    # ===== OPÇÕES DE LIMPEZA =====
    limpar_registros_periodo = forms.BooleanField(
        label="Limpar registros do período selecionado",
        required=False,
        initial=True,
        help_text="Se marcado, remove os registros existentes apenas no período de datas selecionado antes da importação",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    limpar_toda_base = forms.BooleanField(
        label="Limpar TODA a base de vendas",
        required=False,
        initial=False,
        help_text="⚠️ ATENÇÃO: Remove TODAS as vendas existentes, independente da data",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # ===== ARQUIVOS AUXILIARES (OPCIONAIS) =====
    arquivo_produtos = forms.FileField(
        label="Planilha de Produtos (Opcional)",
        required=False,
        help_text="Planilha Excel com códigos e descrições dos produtos",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls'})
    )
    
    arquivo_classes = forms.FileField(
        label="Planilha de Classes (Opcional)",
        required=False,
        help_text="Planilha Excel com códigos e descrições das classes de produto",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls'})
    )
    
    arquivo_fabricantes = forms.FileField(
        label="Planilha de Fabricantes (Opcional)",
        required=False,
        help_text="Planilha Excel com códigos e descrições dos fabricantes",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls'})
    )
    
    # ===== CONFIGURAÇÃO ADICIONAL =====
    verificar_dependencias = forms.BooleanField(
        label="Verificar dependências (clientes, produtos, etc.)",
        required=False,
        initial=True,
        help_text="Verifica e atualiza automaticamente dados de clientes, produtos e vendedores necessários",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get('data_inicio')
        data_fim = cleaned_data.get('data_fim')
        limpar_periodo = cleaned_data.get('limpar_registros_periodo')
        limpar_toda_base = cleaned_data.get('limpar_toda_base')
        
        # Validar datas
        if data_inicio and data_fim and data_inicio > data_fim:
            self.add_error('data_fim', "Data de fim deve ser maior ou igual à data de início")
        
        # Não permitir ambas as opções de limpeza
        if limpar_periodo and limpar_toda_base:
            self.add_error('limpar_toda_base', "Escolha apenas uma opção de limpeza")
        
        # Se escolheu limpar período, deve informar pelo menos uma data
        if limpar_periodo and not (data_inicio or data_fim):
            self.add_error('limpar_registros_periodo', 
                          "Para limpar por período, informe pelo menos uma data (início ou fim)")
        
        return cleaned_data

# Formulário para processo de sincronização com a Receita Federal
class SincronizarReceitaForm(forms.Form):
    arquivo_csv = forms.FileField(
        label="Arquivo CSV da Receita Federal",
        help_text="Selecione o arquivo CSV com os dados da Receita Federal para sincronização",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )
    
    atualizar_existentes = forms.BooleanField(
        label="Atualizar registros existentes",
        required=False,
        initial=True,
        help_text="Se marcado, os registros existentes serão atualizados com os novos dados",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

# Formulário para sincronização completa
class SincronizacaoCompletaForm(forms.Form):
    sincronizar_lojas = forms.BooleanField(
        label="Sincronizar Lojas",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    sincronizar_vendedores = forms.BooleanField(
        label="Sincronizar Vendedores",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    sincronizar_grupos = forms.BooleanField(
        label="Sincronizar Grupos de Produto",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    sincronizar_produtos = forms.BooleanField(
        label="Sincronizar Produtos",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    sincronizar_clientes = forms.BooleanField(
        label="Sincronizar Clientes",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    atualizar_existentes = forms.BooleanField(
        label="Atualizar registros existentes",
        required=False,
        initial=True,
        help_text="Se marcado, os registros existentes serão atualizados com os novos dados",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    verificar_receita = forms.BooleanField(
        label="Verificar dados na Receita Federal",
        required=False,
        initial=False,
        help_text="Consulta dados de CPF/CNPJ na Receita Federal para clientes novos ou desatualizados",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class VendasForm(forms.ModelForm):
    # ===== CAMPOS VIRTUAIS PARA DISPLAY =====
    
    # Campo virtual para mostrar nome do vendedor da NF
    nome_vendedor_nf_display = forms.CharField(
        label="Nome do Vendedor (NF)",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': True,
            'placeholder': 'Preenchido automaticamente'
        })
    )
    
    # Campo virtual para mostrar vendedor atual do cliente
    vendedor_atual_cliente_display = forms.CharField(
        label="Vendedor Atual do Cliente",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': True,
            'placeholder': 'Baseado no cliente selecionado',
            'style': 'background-color: #f8f9fa;'
        })
    )
    
    class Meta:
        model = Vendas
        fields = [
            # ===== RELACIONAMENTOS =====
            'loja', 'cliente', 'produto', 'grupo_produto', 'fabricante',
            
            # ===== VENDEDOR HISTÓRICO =====
            'vendedor_nf',  # ÚNICO campo de vendedor
            
            # ===== DADOS DA VENDA =====
            'data_venda', 'quantidade', 'valor_total', 
            
            # ===== DADOS DA NF =====
            'numero_nf', 'serie_nf', 'estado'
        ]
        
        widgets = {
            # ===== RELACIONAMENTOS =====
            'loja': forms.Select(attrs={'class': 'form-select'}),
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'produto': forms.Select(attrs={'class': 'form-select'}),
            'grupo_produto': forms.Select(attrs={
                'class': 'form-select',
                'readonly': True,
                'style': 'background-color: #f8f9fa; pointer-events: none;'
            }),
            'fabricante': forms.Select(attrs={
                'class': 'form-select',
                'readonly': True,
                'style': 'background-color: #f8f9fa; pointer-events: none;'
            }),
            
            # ===== VENDEDOR =====
            'vendedor_nf': forms.TextInput(attrs={
                'class': 'form-control', 
                'maxlength': '3',
                'placeholder': 'Código do vendedor da NF (3 dígitos)'
            }),
            
            # ===== DADOS DA VENDA =====
            'data_venda': CustomDateInput(attrs={'class': 'form-control'}),
            'quantidade': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01',
                'min': '0'
            }),
            'valor_total': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01',
                'min': '0'
            }),
            
            # ===== DADOS DA NF =====
            'numero_nf': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número da Nota Fiscal'
            }),
            'serie_nf': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '3',
                'placeholder': 'Série'
            }),
            'estado': forms.TextInput(attrs={
                'class': 'form-control', 
                'maxlength': '2',
                'placeholder': 'UF'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Tornar alguns campos obrigatórios
        self.fields['loja'].required = True
        self.fields['cliente'].required = True
        self.fields['produto'].required = True
        self.fields['data_venda'].required = True
        self.fields['quantidade'].required = True
        self.fields['valor_total'].required = True
        
        # ===== PREENCHER CAMPOS VIRTUAIS =====
        if self.instance and self.instance.pk:
            # Para edição - preencher campos virtuais
            self.fields['nome_vendedor_nf_display'].initial = self.instance.vendedor_nf_nome
            
            if self.instance.cliente and self.instance.cliente.codigo_vendedor:
                vendedor_atual = f"{self.instance.cliente.codigo_vendedor} - {self.instance.cliente.nome_vendedor}"
                self.fields['vendedor_atual_cliente_display'].initial = vendedor_atual
        
        elif self.data and self.data.get('vendedor_nf'):
            # Para formulário sendo submetido - buscar nome do vendedor da NF
            codigo_vendedor_nf = self.data.get('vendedor_nf')
            if codigo_vendedor_nf and len(codigo_vendedor_nf) == 3:
                try:
                    vendedor = Vendedor.objects.get(codigo=codigo_vendedor_nf, ativo=True)
                    self.fields['nome_vendedor_nf_display'].initial = vendedor.nome
                except Vendedor.DoesNotExist:
                    self.fields['nome_vendedor_nf_display'].initial = 'Vendedor não encontrado'
        
        # Configurar grupo e fabricante como readonly visual
        self.fields['grupo_produto'].widget.attrs.update({
            'tabindex': '-1',
            'title': 'Preenchido automaticamente pelo produto'
        })
        self.fields['fabricante'].widget.attrs.update({
            'tabindex': '-1',
            'title': 'Preenchido automaticamente pelo produto'
        })
    
    def clean_vendedor_nf(self):
        """Validação específica para código do vendedor da NF"""
        codigo = self.cleaned_data.get('vendedor_nf')
        if codigo:
            # Normalizar para 3 dígitos
            codigo = str(codigo).zfill(3)
            
            # Validar formato
            if len(codigo) != 3 or not codigo.isdigit():
                raise forms.ValidationError("O código do vendedor deve ter exatamente 3 dígitos numéricos.")
            
            # Verificar se vendedor existe (warning, não erro)
            if not Vendedor.objects.filter(codigo=codigo, ativo=True).exists():
                # Para dados históricos, permitir vendedores inativos
                if not Vendedor.objects.filter(codigo=codigo).exists():
                    raise forms.ValidationError(f"Vendedor com código {codigo} não encontrado.")
            
            return codigo
        return codigo
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validar se grupo_produto e fabricante correspondem ao produto
        produto = cleaned_data.get('produto')
        grupo_produto = cleaned_data.get('grupo_produto')
        fabricante = cleaned_data.get('fabricante')
        
        if produto:
            if grupo_produto and produto.grupo != grupo_produto:
                self.add_error('grupo_produto', 'Grupo de produto não corresponde ao produto selecionado.')
            
            if fabricante and produto.fabricante != fabricante:
                self.add_error('fabricante', 'Fabricante não corresponde ao produto selecionado.')
        
        return cleaned_data

# ===== FORMULÁRIO PARA ATUALIZAR BI.DBF (CLIPPER) =====
class AtualizarBIForm(forms.Form):
    """
    Formulário para atualizar BI.DBF diretamente do Clipper
    Replica a interface do programa ATBI.PRG
    """
    
    # Choices para meses
    MESES_CHOICES = [
        ('01', 'Janeiro'),
        ('02', 'Fevereiro'), 
        ('03', 'Março'),
        ('04', 'Abril'),
        ('05', 'Maio'),
        ('06', 'Junho'),
        ('07', 'Julho'),
        ('08', 'Agosto'),
        ('09', 'Setembro'),
        ('10', 'Outubro'),
        ('11', 'Novembro'),
        ('12', 'Dezembro'),
    ]
    
    # Gerar anos dinamicamente (últimos 5 anos em formato YY)
    ano_atual = datetime.now().year - 2000  # Formato YY como no Clipper
    ANOS_CHOICES = [
        (str(ano).zfill(2), str(2000 + ano)) 
        for ano in range(ano_atual - 4, ano_atual + 1)
    ]
    
    mes = forms.ChoiceField(
        label="Mês de Referência",
        choices=MESES_CHOICES,
        initial=str(datetime.now().month).zfill(2),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    ano = forms.ChoiceField(
        label="Ano de Referência", 
        choices=ANOS_CHOICES,
        initial=str(datetime.now().year - 2000).zfill(2),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    limpar_registros_anteriores = forms.BooleanField(
        label="Limpar registros anteriores",
        required=False,
        initial=True,
        help_text="Se marcado, os registros existentes para o mês/ano selecionado serão removidos antes da importação",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    verificar_dependencias = forms.BooleanField(
        label="Verificar dependências (clientes, produtos, etc.)",
        required=False,
        initial=True,
        help_text="Verifica e atualiza automaticamente dados de clientes, produtos e vendedores necessários",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    notificar_conclusao = forms.BooleanField(
        label="Notificar quando concluir",
        required=False,
        initial=False,
        help_text="Enviar notificação por e-mail quando a sincronização for concluída",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        mes = cleaned_data.get('mes')
        ano = cleaned_data.get('ano')
        
        # Validar se mês e ano são válidos
        if mes and ano:
            try:
                mes_int = int(mes)
                ano_int = int(ano) + 2000  # Converter YY para YYYY
                
                if mes_int < 1 or mes_int > 12:
                    self.add_error('mes', "Mês deve estar entre 01 e 12")
                
                if ano_int < 2020 or ano_int > 2030:
                    self.add_error('ano', "Ano deve estar entre 2020 e 2030")
                    
            except ValueError:
                self.add_error('mes', "Valores de mês/ano inválidos")
        
        return cleaned_data
