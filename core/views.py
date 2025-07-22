# core/views.py - Login View com nome mais apropriado

from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from core.models import PerfilUsuario, Usuario
from core.forms import UsuarioForm

# Em core/views.py, SUBSTITUA a PortalLoginView existente por esta versão:

class PortalLoginView(LoginView):
    """
    View de login inteligente que redireciona baseado no nível do usuário
    """
    template_name = 'login.html'  # ✅ Usa o template existente
    
    def form_valid(self, form):
        user = form.get_user()
        print(f"✅ Login bem-sucedido para: {user.username} (nível: {getattr(user, 'nivel', 'N/A')})")
        return super().form_valid(form)
    
    def get_success_url(self):
        """Determina URL de redirecionamento baseado no nível do usuário"""
        user = self.request.user
        
        print(f"🔍 Determinando redirecionamento para usuário: {user.username}")
        
        # Se é superuser, vai para gestor
        if user.is_superuser:
            print("🔧 Superuser - redirecionando para /gestor/")
            return '/gestor/'
        
        # Se não tem nível definido, vai para vendedor (fallback seguro)
        if not hasattr(user, 'nivel') or not user.nivel:
            print("⚠️ Usuário sem nível - redirecionando para /vendedor/")
            return '/vendedor/'
        
        # Redirecionamento baseado no nível
        if user.nivel == 'admin':
            print("👨‍💼 Admin - redirecionando para /gestor/")
            return '/gestor/'
        elif user.nivel == 'gestor':
            print("👨‍💼 Gestor - redirecionando para /gestor/")  
            return '/gestor/'
        elif user.nivel == 'vendedor':
            print("🛍️ Vendedor - redirecionando para /vendedor/")
            return '/vendedor/'
        else:
            print(f"❓ Nível desconhecido ({user.nivel}) - redirecionando para /vendedor/")
            return '/vendedor/'
 
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['app_name'] = 'Portal Comercial'
        return context

def home_view(request):
    """View da página inicial"""
    return render(request, 'home.html')

@login_required
def perfil(request):
    """View do perfil do usuário"""
    # Determinar URL de volta baseada no nível do usuário
    if hasattr(request.user, 'nivel'):
        if request.user.nivel in ['admin', 'gestor']:
            back_url = 'gestor:home'
        elif request.user.nivel == 'vendedor':
            back_url = 'vendedor:home'
        else:
            back_url = 'home'
    else:
        back_url = 'home'
    
    if request.method == 'POST':
        # Processar alterações do perfil
        usuario = request.user
        
        # Atualizar campos básicos
        usuario.first_name = request.POST.get('first_name', '')
        usuario.last_name = request.POST.get('last_name', '')
        usuario.email = request.POST.get('email', '')
        usuario.telefone = request.POST.get('telefone', '')
        
        # Processar nova senha se fornecida
        nova_senha = request.POST.get('nova_senha', '')
        if nova_senha:
            usuario.set_password(nova_senha)
        
        # Processar upload de foto se fornecida
        foto = request.FILES.get('foto')
        if foto:
            # Aqui você implementaria o upload da foto
            # usuario.foto_perfil = foto
            pass
        
        usuario.save()
        messages.success(request, 'Perfil atualizado com sucesso!')
        return redirect('perfil')
    
    context = {
        'usuario': request.user,
        'back_url': back_url,
    }
    
    return render(request, 'perfil.html', context)

def logout_view(request):
    """View de logout personalizada"""
    user_nivel = getattr(request.user, 'nivel', None) if request.user.is_authenticated else None
    logout(request)
    
    # Mensagem personalizada baseada no nível
    if user_nivel == 'vendedor':
        messages.success(request, 'Logout realizado com sucesso! Volte sempre.')
    elif user_nivel in ['admin', 'gestor']:
        messages.success(request, 'Sessão encerrada com sucesso!')
    else:
        messages.success(request, 'Até logo!')
    
    return redirect('login')

# CRUD USUÁRIO

@login_required
def usuario_list(request):
    # Ordena por username para garantir consistência na paginação
    usuarios_list = Usuario.objects.all().order_by('username')
    
    # Configurar paginação (10 itens por página)
    paginator = Paginator(usuarios_list, 10)
    page = request.GET.get('page', 1)
    
    try:
        usuarios = paginator.page(page)
    except PageNotAnInteger:
        # Se a página não for um inteiro, exibe a primeira página
        usuarios = paginator.page(1)
    except EmptyPage:
        # Se a página estiver fora do intervalo, exibe a última página
        usuarios = paginator.page(paginator.num_pages)
    
    return render(request, 'gestor/usuario_list.html', {'usuarios': usuarios})

@login_required
def usuario_create(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuário criado com sucesso.')
            # Limpa todas as mensagens após adicionar para evitar duplicação
            storage = messages.get_messages(request)
            storage.used = True
            return redirect('gestor:usuario_list')
    else:
        form = UsuarioForm()
    return render(request, 'gestor/usuario_form.html', {'form': form})

@login_required
def usuario_update(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        form = UsuarioForm(request.POST, request.FILES, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuário atualizado com sucesso.')
            # Limpa todas as mensagens após adicionar para evitar duplicação
            storage = messages.get_messages(request)
            storage.used = True
            return redirect('gestor:usuario_list')
    else:
        form = UsuarioForm(instance=usuario)
    return render(request, 'gestor/usuario_form.html', {'form': form})

@login_required
def usuario_toggle_status(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    usuario.is_active = not usuario.is_active
    usuario.save()
    
    status_text = "ativado" if usuario.is_active else "desativado"
    messages.success(request, f'Usuário {usuario.username} {status_text} com sucesso.')
    
    return redirect('gestor:usuario_list')