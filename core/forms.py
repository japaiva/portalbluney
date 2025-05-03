# core/forms.py (adicionar ao arquivo existente)
from django import forms
from core.models import Cliente, ClienteContato, ClienteItem, Usuario
from django.contrib.auth.hashers import make_password

class UsuarioForm(forms.ModelForm):
    confirm_password = forms.CharField(widget=forms.PasswordInput(), required=False)
    password = forms.CharField(widget=forms.PasswordInput(), required=False)
    
    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'nivel', 'telefone', 'is_active']
        widgets = {
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'nivel': forms.Select(attrs={'class': 'form-select'}),
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

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['codigo', 'nome', 'endereco', 'cidade', 'estado', 'cep', 
                  'telefone', 'email', 'observacoes', 'ativo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-select'}, choices=[('', '---')] + [(s, s) for s in ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']]),
            'cep': forms.TextInput(attrs={'class': 'form-control', 'data-mask': '00000-000'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'data-mask': '(00) 00000-0000'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

# Formulário para ClienteItem (atualizado com campo código)
class ClienteItemForm(forms.ModelForm):
    class Meta:
        model = ClienteItem
        fields = ['codigo', 'cpf_cnpj', 'nome_razao', 'tipo', 'ativo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf_cnpj': forms.TextInput(attrs={'class': 'form-control', 'data-mask': '000.000.000-00'}),
            'nome_razao': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
    def clean_cpf_cnpj(self):
        cpf_cnpj = self.cleaned_data['cpf_cnpj']
        # Remove caracteres não numéricos
        return ''.join(filter(str.isdigit, cpf_cnpj))

# Formulário para ClienteContato (renomeado de ContatoForm)
class ClienteContatoForm(forms.ModelForm):
    class Meta:
        model = ClienteContato
        fields = ['nome', 'whatsapp', 'cargo', 'principal', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'whatsapp': forms.TextInput(attrs={'class': 'form-control', 'data-mask': '(00) 00000-0000'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),
            'principal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }