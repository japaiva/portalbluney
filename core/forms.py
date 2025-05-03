# core/forms.py
from django import forms
from core.models import (Cliente, ClienteContato, Usuario, 
                        Loja, Vendedor, Produto, ClasseProduto, RegistroBI, LogSincronizacao)
from django.contrib.auth.hashers import make_password
from datetime import datetime
import calendar

class UsuarioForm(forms.ModelForm):
    confirm_password = forms.CharField(widget=forms.PasswordInput(), required=False)
    password = forms.CharField(widget=forms.PasswordInput(), required=False)
    
    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'nivel', 'telefone', 
                  'codigo_loja', 'codigo_vendedor', 'is_active']
        widgets = {
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'nivel': forms.Select(attrs={'class': 'form-select'}),
            'codigo_loja': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '3'}),
            'codigo_vendedor': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '3'}),
        }
    
    def __init__(self, *args, **kwargs):
        super(UsuarioForm, self).__init__(*args, **kwargs)
        
        # Se estiver editando um usuário existente, não exigir senha
        if self.instance.pk:
            self.fields['password'].required = False
            self.fields['confirm_password'].required = False
        else:
            self.fields['password'].required = True
            self.fields['confirm_password'].required = True
        
        # Adicionar atributos de classe para os widgets que não foram especificados
        for field_name, field in self.fields.items():
            if not hasattr(field.widget, 'attrs') or 'class' not in field.widget.attrs:
                if isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs['class'] = 'form-check-input'
                else:
                    field.widget.attrs['class'] = 'form-control'
    
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
        user = super().save(commit=False)
        
        # Se uma senha foi fornecida, codificá-la
        password = self.cleaned_data.get('password')
        if password:
            user.password = make_password(password)
        
        if commit:
            user.save()
        
        return user


from django import forms
from core.models import Cliente
from django.utils import timezone

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            # Campos de identificação
            'codigo', 'codigo_master', 'nome', 'nome_fantasia',
            
            # Campos de endereço
            'tipo_logradouro', 'endereco', 'numero', 'complemento', 'bairro', 
            'cidade', 'estado', 'cep',
            
            # Campos de contato
            'telefone', 'email',
            
            # Dados fiscais
            'cpf_cnpj', 'tipo_documento', 'nome_razao_social',
            'inscricao_estadual', 'inscricao_municipal',
            
            # Informações da Receita
            'situacao_cadastral', 'data_situacao_cadastral',
            'cnae_principal', 'cnae_descricao', 'porte_empresa',
            'natureza_juridica', 'data_abertura', 'data_ultima_verificacao',
            'opcao_pelo_simples', 'opcao_pelo_mei',
            
            # Dados comerciais
            'codigo_loja', 'codigo_vendedor', 'nome_vendedor',
            'data_cadastro', 'data_ultima_compra',
            
            # Outros
            'observacoes', 'ativo'
        ]
        widgets = {
            # Campos de identificação
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_master': forms.TextInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'nome_fantasia': forms.TextInput(attrs={'class': 'form-control'}),
            
            # Campos de endereço
            'tipo_logradouro': forms.Select(attrs={'class': 'form-select'}, 
                               choices=[('', '---')] + [(t, t) for t in [
                                   'Rua', 'Avenida', 'Alameda', 'Estrada', 'Rodovia', 
                                   'Praça', 'Travessa', 'Quadra', 'Condomínio', 'Outros'
                               ]]),
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
            
            # Campos de contato
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'data-mask': '(00) 00000-0000'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            
            # Dados fiscais
            'cpf_cnpj': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-select'}),
            'nome_razao_social': forms.TextInput(attrs={'class': 'form-control'}),
            'inscricao_estadual': forms.TextInput(attrs={'class': 'form-control'}),
            'inscricao_municipal': forms.TextInput(attrs={'class': 'form-control'}),
            
            # Informações da Receita
            'situacao_cadastral': forms.TextInput(attrs={'class': 'form-control'}),
            'data_situacao_cadastral': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'cnae_principal': forms.TextInput(attrs={'class': 'form-control'}),
            'cnae_descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'porte_empresa': forms.TextInput(attrs={'class': 'form-control'}),
            'natureza_juridica': forms.TextInput(attrs={'class': 'form-control'}),
            'data_abertura': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_ultima_verificacao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'opcao_pelo_simples': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'opcao_pelo_mei': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
            # Dados comerciais
            'codigo_loja': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '3'}),
            'codigo_vendedor': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '3'}),
            'nome_vendedor': forms.TextInput(attrs={'class': 'form-control'}),
            'data_cadastro': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_ultima_compra': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            
            # Outros
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super(ClienteForm, self).__init__(*args, **kwargs)
        
        # Tornar alguns campos obrigatórios
        self.fields['codigo'].required = True
        self.fields['nome'].required = True
        
        # Se for uma nova instância (sem ID), preencher data de cadastro
        if not self.instance.pk and not self.data.get('data_cadastro'):
            self.initial['data_cadastro'] = timezone.now().date()
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validação para códigos de loja e vendedor
        codigo_loja = cleaned_data.get('codigo_loja')
        if codigo_loja and (len(codigo_loja) != 3 or not codigo_loja.isdigit()):
            self.add_error('codigo_loja', "O código da loja deve ter exatamente 3 dígitos numéricos.")
        
        codigo_vendedor = cleaned_data.get('codigo_vendedor')
        if codigo_vendedor and (len(codigo_vendedor) != 3 or not codigo_vendedor.isdigit()):
            self.add_error('codigo_vendedor', "O código do vendedor deve ter exatamente 3 dígitos numéricos.")
        
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
        
        # Validação do código master (se informado, deve existir)
        codigo_master = cleaned_data.get('codigo_master')
        if codigo_master:
            # Verificar se o código existe no banco de dados
            existe = Cliente.objects.filter(codigo=codigo_master).exists()
            if not existe:
                self.add_error('codigo_master', "Código master não existe no cadastro de clientes.")
        
        return cleaned_data
class ClienteContatoForm(forms.ModelForm):
    class Meta:
        model = ClienteContato
        fields = ['codigo', 'codigo_master', 'nome', 'whatsapp', 'cargo', 'principal', 'ativo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_master': forms.TextInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'whatsapp': forms.TextInput(attrs={'class': 'form-control', 'data-mask': '(00) 00000-0000'}),
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

class ClasseProdutoForm(forms.ModelForm):
    class Meta:
        model = ClasseProduto
        fields = ['codigo', 'descricao', 'ativo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '4'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_codigo(self):
        codigo = self.cleaned_data['codigo']
        if len(codigo) != 4 or not codigo.isdigit():
            raise forms.ValidationError("O código da classe de produto deve ter exatamente 4 dígitos numéricos.")
        return codigo

class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['codigo', 'descricao', 'classe', 'preco', 'ativo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '6'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'classe': forms.Select(attrs={'class': 'form-select'}),
            'preco': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_codigo(self):
        codigo = self.cleaned_data['codigo']
        if len(codigo) != 6 or not codigo.isdigit():
            raise forms.ValidationError("O código do produto deve ter exatamente 6 dígitos numéricos.")
        return codigo

# Formulário para processo de sincronização com o BI
class SincronizarBIForm(forms.Form):
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
    
    # Gerar anos dinamicamente, mostrando apenas os últimos 5 anos
    ano_atual = datetime.now().year - 2000  # No formato YY como no Clipper
    ANOS_CHOICES = [(str(ano).zfill(2), str(2000 + ano)) for ano in range(ano_atual - 4, ano_atual + 1)]
    
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
    
    cache_local = forms.BooleanField(
        label="Armazenar cópia local dos dados",
        required=False,
        initial=False,
        help_text="Mantém uma cópia local dos dados para acesso offline (útil para relatórios)",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    notificar_conclusao = forms.BooleanField(
        label="Notificar quando concluir",
        required=False,
        initial=False,
        help_text="Enviar notificação por e-mail quando a sincronização for concluída",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    periodo_completo = forms.BooleanField(
        label="Período completo (considerar todo o mês)",
        required=False,
        initial=True,
        help_text="Se desmarcado, você pode especificar um intervalo de dias específico",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'data-bs-toggle': 'collapse',
            'data-bs-target': '#collapsePeriodo',
            'aria-expanded': 'true',
            'aria-controls': 'collapsePeriodo'
        })
    )
    
    dia_inicial = forms.IntegerField(
        label="Dia inicial",
        required=False,
        min_value=1,
        max_value=31,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    dia_final = forms.IntegerField(
        label="Dia final",
        required=False,
        min_value=1,
        max_value=31,
        initial=lambda: calendar.monthrange(datetime.now().year, datetime.now().month)[1],
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validação apenas se período completo não estiver marcado
        if not cleaned_data.get('periodo_completo'):
            dia_inicial = cleaned_data.get('dia_inicial')
            dia_final = cleaned_data.get('dia_final')
            
            # Validar se os dias foram informados
            if dia_inicial is None:
                self.add_error('dia_inicial', "Dia inicial é obrigatório quando período completo não está selecionado")
            
            if dia_final is None:
                self.add_error('dia_final', "Dia final é obrigatório quando período completo não está selecionado")
            
            # Validar se dia final é maior ou igual ao dia inicial
            if dia_inicial and dia_final and dia_inicial > dia_final:
                self.add_error('dia_final', "Dia final deve ser maior ou igual ao dia inicial")
            
            # Validar se os dias são válidos para o mês/ano selecionado
            if dia_inicial and dia_final and 'mes' in cleaned_data and 'ano' in cleaned_data:
                mes = int(cleaned_data.get('mes'))
                ano = int(cleaned_data.get('ano')) + 2000  # Converter de YY para YYYY
                
                _, ultimo_dia = calendar.monthrange(ano, mes)
                
                if dia_inicial > ultimo_dia:
                    self.add_error('dia_inicial', f"O mês {mes}/{ano} tem apenas {ultimo_dia} dias")
                
                if dia_final > ultimo_dia:
                    self.add_error('dia_final', f"O mês {mes}/{ano} tem apenas {ultimo_dia} dias")
        
        return cleaned_data

# Formulário para processo de sincronização com o BI (versão anterior - compatibilidade)
class SincronizarBIForm_Old(forms.Form):
    arquivo_csv = forms.FileField(
        label="Arquivo CSV do BI",
        help_text="Selecione o arquivo CSV com os dados do BI para sincronização",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )
    
    mes = forms.ChoiceField(
        label="Mês de Referência",
        choices=[(i, i) for i in range(1, 13)],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    ano = forms.ChoiceField(
        label="Ano de Referência",
        choices=[(i, i) for i in range(2020, 2026)],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    limpar_registros_anteriores = forms.BooleanField(
        label="Limpar registros anteriores",
        required=False,
        initial=True,
        help_text="Se marcado, os registros existentes para o mês/ano selecionado serão removidos antes da importação",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

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
    
    sincronizar_classes = forms.BooleanField(
        label="Sincronizar Classes de Produto",
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