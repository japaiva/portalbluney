# core/forms.py
from django import forms
from core.models import (Cliente, ClienteContato, ClienteCnaeSecundario, Usuario, 
                        Loja, Vendedor, Produto, GrupoProduto, Fabricante, Vendas)
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from datetime import datetime
import calendar

# ===== FORMULÁRIO DE USUÁRIO =====

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

# ===== FORMULÁRIOS DE CADASTROS BÁSICOS =====

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

class FabricanteForm(forms.ModelForm):
    class Meta:
        model = Fabricante
        fields = ['codigo', 'descricao', 'ativo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '10'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

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

# Adicione esta versão corrigida do ProdutoForm ao seu core/forms.py

class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['codigo', 'descricao', 'grupo', 'fabricante', 'ativo']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control', 
                'maxlength': '6',
                'placeholder': 'Ex: 123456'
            }),
            'descricao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descrição completa do produto'
            }),
            'grupo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'fabricante': forms.Select(attrs={
                'class': 'form-select'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Tornar campos obrigatórios
        self.fields['codigo'].required = True
        self.fields['descricao'].required = True
        self.fields['grupo'].required = True
        self.fields['fabricante'].required = True
        
        # Adicionar opção vazia para campos de relacionamento
        self.fields['grupo'].empty_label = "Selecione um grupo"
        self.fields['fabricante'].empty_label = "Selecione um fabricante"
        
        # Se não houver grupos ou fabricantes cadastrados, mostrar mensagem
        if not self.fields['grupo'].queryset.exists():
            self.fields['grupo'].empty_label = "Nenhum grupo cadastrado"
        if not self.fields['fabricante'].queryset.exists():
            self.fields['fabricante'].empty_label = "Nenhum fabricante cadastrado"
    
    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo', '').strip()
        
        if not codigo:
            raise forms.ValidationError("Código é obrigatório.")
        
        if len(codigo) != 6:
            raise forms.ValidationError("O código deve ter exatamente 6 dígitos.")
        
        if not codigo.isdigit():
            raise forms.ValidationError("O código deve conter apenas números.")
        
        # Verificar se o código já existe (excluindo a instância atual em caso de edição)
        existing = Produto.objects.filter(codigo=codigo)
        if self.instance and self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise forms.ValidationError(f"Já existe um produto com o código '{codigo}'.")
        
        return codigo
    
    def clean_descricao(self):
        descricao = self.cleaned_data.get('descricao', '').strip()
        
        if not descricao:
            raise forms.ValidationError("Descrição é obrigatória.")
        
        if len(descricao) < 3:
            raise forms.ValidationError("Descrição deve ter pelo menos 3 caracteres.")
        
        return descricao.title()  # Capitalizar descrição
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validar se grupo e fabricante existem e estão ativos
        grupo = cleaned_data.get('grupo')
        fabricante = cleaned_data.get('fabricante')
        
        if grupo and not grupo.ativo:
            self.add_error('grupo', 'O grupo selecionado está inativo.')
        
        if fabricante and not fabricante.ativo:
            self.add_error('fabricante', 'O fabricante selecionado está inativo.')
        
        return cleaned_data
    
    def save(self, commit=True):
        produto = super().save(commit=False)
        
        # Garantir que o código seja salvo com zeros à esquerda
        if produto.codigo:
            produto.codigo = produto.codigo.zfill(6)
        
        if commit:
            produto.save()
        
        return produto

# ===== FORMULÁRIO DO CLIENTE ATUALIZADO =====

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            # ===== INFORMAÇÕES PRINCIPAIS =====
            'codigo', 'codigo_master', 'nome', 'nome_fantasia', 'status',
            
            # ===== DADOS FISCAIS =====
            'tipo_documento', 'cpf_cnpj', 'nome_razao_social',
            'inscricao_estadual', 'inscricao_municipal', 'situacao_cadastral',
            
            # ===== ENDEREÇO COMPLETO =====
            'tipo_logradouro', 'endereco', 'numero', 'complemento', 
            'bairro', 'cidade', 'estado', 'cep',
            
            # ===== RECEITA FEDERAL - INFORMAÇÕES =====
            'cnae_principal', 'cnae_descricao', 'porte_empresa',
            'natureza_juridica', 'data_abertura', 'data_ultima_verificacao',
            'opcao_pelo_simples', 'opcao_pelo_mei',
            
            # ===== INFORMAÇÕES COMERCIAIS =====
            'codigo_loja', 'codigo_vendedor', 'nome_vendedor',
            'data_cadastro', 'data_ultima_compra',
            
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
            
            # ===== DADOS FISCAIS =====
            'tipo_documento': forms.Select(attrs={'class': 'form-select'}),
            'cpf_cnpj': forms.TextInput(attrs={'class': 'form-control'}),
            'nome_razao_social': forms.TextInput(attrs={'class': 'form-control'}),
            'inscricao_estadual': forms.TextInput(attrs={'class': 'form-control'}),
            'inscricao_municipal': forms.TextInput(attrs={'class': 'form-control'}),
            'situacao_cadastral': forms.TextInput(attrs={'class': 'form-control'}),
            
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
            'data_abertura': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_ultima_verificacao': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'opcao_pelo_simples': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'opcao_pelo_mei': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
            # ===== INFORMAÇÕES COMERCIAIS =====
            'codigo_loja': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '3'}),
            'codigo_vendedor': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '3'}),
            'nome_vendedor': forms.TextInput(attrs={'class': 'form-control'}),
            'data_cadastro': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'data_ultima_compra': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            
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
        
        # Se for uma nova instância (sem ID), preencher data de cadastro
        if not self.instance.pk and not self.data.get('data_cadastro'):
            self.initial['data_cadastro'] = timezone.now().strftime('%Y-%m-%dT%H:%M')
    
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

# ===== FORMULÁRIOS RELACIONADOS AO CLIENTE =====

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

class ClienteCnaeSecundarioForm(forms.ModelForm):
    class Meta:
        model = ClienteCnaeSecundario
        fields = ['codigo_cnae', 'descricao_cnae', 'ordem']
        widgets = {
            'codigo_cnae': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ex: 4761003',
                'maxlength': '10'
            }),
            'descricao_cnae': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Descrição da atividade'
            }),
            'ordem': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '1',
                'value': '1'
            }),
        }
    
    def clean_codigo_cnae(self):
        codigo = self.cleaned_data['codigo_cnae']
        if not codigo.isdigit():
            raise forms.ValidationError("Código CNAE deve conter apenas números")
        return codigo

# FormSet para múltiplos CNAEs
ClienteCnaeSecundarioFormSet = forms.inlineformset_factory(
    Cliente, 
    ClienteCnaeSecundario,
    form=ClienteCnaeSecundarioForm,
    extra=1,  # Quantos formulários vazios mostrar
    can_delete=True,  # Permitir exclusão
    min_num=0,  # Mínimo de CNAEs (opcional)
    max_num=10,  # Máximo de CNAEs secundários
)

class VendasForm(forms.ModelForm):
    class Meta:
        model = Vendas
        fields = [
            'data_venda', 'cliente', 'produto', 'grupo_produto', 'fabricante', 
            'loja', 'vendedor', 'vendedor_nf', 'quantidade', 'valor_total', 
            'numero_nf', 'estado'
        ]
        widgets = {
            'data_venda': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date'
            }),
            'cliente': forms.Select(attrs={
                'class': 'form-select',
                'data-live-search': 'true'
            }),
            'produto': forms.Select(attrs={
                'class': 'form-select',
                'data-live-search': 'true'
            }),
            'grupo_produto': forms.Select(attrs={
                'class': 'form-select',
                'readonly': True
            }),
            'fabricante': forms.Select(attrs={
                'class': 'form-select', 
                'readonly': True
            }),
            'loja': forms.Select(attrs={'class': 'form-select'}),
            'vendedor': forms.Select(attrs={'class': 'form-select'}),
            'vendedor_nf': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Vendedor da época',
                'maxlength': '3'
            }),
            'quantidade': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01',
                'min': '0',
                'placeholder': '0,00'
            }),
            'valor_total': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01',
                'min': '0',
                'placeholder': '0,00'
            }),
            'numero_nf': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número da Nota Fiscal'
            }),
            'estado': forms.TextInput(attrs={
                'class': 'form-control', 
                'maxlength': '2',
                'placeholder': 'UF (ex: SP)',
                'style': 'text-transform: uppercase;'
            }),
        }
        labels = {
            'data_venda': 'Data da Venda',
            'cliente': 'Cliente', 
            'produto': 'Produto',
            'grupo_produto': 'Grupo do Produto',
            'fabricante': 'Fabricante',
            'loja': 'Loja',
            'vendedor': 'Vendedor Atual',
            'vendedor_nf': 'Vendedor da NF',
            'quantidade': 'Quantidade',
            'valor_total': 'Valor Total (R$)',
            'numero_nf': 'Número da NF',
            'estado': 'Estado (UF)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Tornar campos obrigatórios
        self.fields['data_venda'].required = True
        self.fields['cliente'].required = True
        self.fields['produto'].required = True
        self.fields['loja'].required = True
        self.fields['vendedor'].required = True
        self.fields['quantidade'].required = True
        self.fields['valor_total'].required = True
        
        # Se estiver editando, preencher grupo e fabricante automaticamente
        if self.instance and self.instance.pk and self.instance.produto:
            self.fields['grupo_produto'].initial = self.instance.produto.grupo
            self.fields['fabricante'].initial = self.instance.produto.fabricante
            # Tornar estes campos readonly
            self.fields['grupo_produto'].widget.attrs['disabled'] = True
            self.fields['fabricante'].widget.attrs['disabled'] = True
        
        # Ordenar e filtrar querysets
        self.fields['cliente'].queryset = Cliente.objects.filter(
            status='ativo'
        ).order_by('nome')
        
        self.fields['produto'].queryset = Produto.objects.filter(
            ativo=True
        ).select_related('grupo', 'fabricante').order_by('descricao')
        
        self.fields['loja'].queryset = Loja.objects.filter(
            ativo=True
        ).order_by('codigo')
        
        self.fields['vendedor'].queryset = Vendedor.objects.filter(
            ativo=True
        ).order_by('nome')
        
        # Adicionar opções vazias para campos obrigatórios
        self.fields['cliente'].empty_label = "Selecione um cliente"
        self.fields['produto'].empty_label = "Selecione um produto"
        self.fields['loja'].empty_label = "Selecione uma loja"
        self.fields['vendedor'].empty_label = "Selecione um vendedor"
        
        # Se não for edição, definir valores padrão
        if not self.instance.pk:
            from datetime import date
            self.fields['data_venda'].initial = date.today()
    
    def clean_estado(self):
        estado = self.cleaned_data.get('estado', '').strip().upper()
        if estado and len(estado) != 2:
            raise forms.ValidationError("Estado deve ter exatamente 2 caracteres (UF)")
        return estado
    
    def clean_vendedor_nf(self):
        vendedor_nf = self.cleaned_data.get('vendedor_nf', '').strip()
        if vendedor_nf and (len(vendedor_nf) > 3 or not vendedor_nf.isdigit()):
            raise forms.ValidationError("Vendedor NF deve ter no máximo 3 dígitos numéricos")
        return vendedor_nf
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validar se produto está ativo
        produto = cleaned_data.get('produto')
        if produto and not produto.ativo:
            self.add_error('produto', 'O produto selecionado está inativo.')
        
        # Validar se cliente está ativo
        cliente = cleaned_data.get('cliente')
        if cliente and cliente.status != 'ativo':
            self.add_error('cliente', 'O cliente selecionado não está ativo.')
        
        # Validar valores numéricos
        quantidade = cleaned_data.get('quantidade')
        valor_total = cleaned_data.get('valor_total')
        
        if quantidade is not None and quantidade <= 0:
            self.add_error('quantidade', 'Quantidade deve ser maior que zero.')
        
        if valor_total is not None and valor_total <= 0:
            self.add_error('valor_total', 'Valor total deve ser maior que zero.')
        
        # Auto-preencher grupo e fabricante baseado no produto
        if produto:
            cleaned_data['grupo_produto'] = produto.grupo
            cleaned_data['fabricante'] = produto.fabricante
        
        return cleaned_data
    
    def save(self, commit=True):
        venda = super().save(commit=False)
        
        # Garantir que grupo e fabricante sejam preenchidos
        if venda.produto:
            venda.grupo_produto = venda.produto.grupo
            venda.fabricante = venda.produto.fabricante
        
        if commit:
            venda.save()
        
        return venda

# ===== FORMULÁRIO PARA IMPORTAÇÃO DE VENDAS =====
class ImportarVendasForm(forms.Form):
    """Formulário simplificado para importação de vendas - apenas campos essenciais"""
    
    # === ARQUIVO PRINCIPAL ===
    arquivo_csv = forms.FileField(
        label="Arquivo BI (Excel/CSV)",
        help_text="Selecione o arquivo principal com dados do BI - processará arquivo completo",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv,.xlsx,.xls'})
    )
    
    # === PLANILHAS AUXILIARES (OPCIONAIS) ===
    arquivo_produtos = forms.FileField(
        label="PRODUTOS.xlsx",
        required=False,
        help_text="Planilha com dados de produtos (opcional)",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls'})
    )

    arquivo_classes = forms.FileField(
        label="CLASSE.xlsx", 
        required=False,
        help_text="Planilha com dados de classes/grupos (opcional)",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls'})
    )

    arquivo_fabricantes = forms.FileField(
        label="FABR.xlsx",
        required=False, 
        help_text="Planilha com dados de fabricantes (opcional)",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls'})
    )
    
    # === CONFIGURAÇÕES BÁSICAS ===
    limpar_registros_anteriores = forms.BooleanField(
        label="Limpar dados anteriores antes da importação",
        required=False,
        initial=True,
        help_text="Remove todos os registros de vendas existentes",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    verificar_dependencias = forms.BooleanField(
        label="Criar/atualizar clientes, produtos e outros dados automaticamente",
        required=False,
        initial=True,
        help_text="Cria automaticamente registros que não existem (clientes, produtos, etc.)",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def clean_arquivo_csv(self):
        arquivo = self.cleaned_data['arquivo_csv']
        
        if arquivo:
            # Verificar tamanho do arquivo (máx 50MB)
            if arquivo.size > 50 * 1024 * 1024:
                raise forms.ValidationError("Arquivo muito grande. Máximo permitido: 50MB")
            
            # Verificar extensão
            nome = arquivo.name.lower()
            if not (nome.endswith('.csv') or nome.endswith('.xlsx') or nome.endswith('.xls')):
                raise forms.ValidationError("Formato não suportado. Use .csv, .xlsx ou .xls")
        
        return arquivo