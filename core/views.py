from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from .models import PerfilUsuario, Usuario
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404
from .forms import UsuarioForm



@login_required
def perfil(request):
    usuario = request.user
    
    # Obter ou criar perfil ao carregar a página
    perfil, created = PerfilUsuario.objects.get_or_create(usuario=usuario)
    
    # Obter o contexto atual do usuário
    app_context = request.session.get('app_context', 'home')
    
    # Determinar para onde voltar com base no contexto
    if app_context == 'gestor':
        back_url = 'gestor:dashboard'
    elif app_context == 'cliente':
        back_url = 'cliente:dashboard'
    elif app_context == 'projetista':
        back_url = 'projetista:dashboard'
    else:
        back_url = 'home'
    
    if request.method == 'POST':
        # Atualizar informações básicas
        usuario.first_name = request.POST.get('first_name', '')
        usuario.last_name = request.POST.get('last_name', '')
        usuario.email = request.POST.get('email', '')
        
        # Atualizar telefone no usuário e no perfil
        telefone = request.POST.get('telefone', '')
        usuario.telefone = telefone
        perfil.telefone = telefone
        
        # Processar foto
        if 'foto' in request.FILES:
            # Código de debug para verificar o upload
            arquivo = request.FILES['foto']
            print(f"Iniciando upload do arquivo: {arquivo.name}")
            
            # Salvar a foto no perfil (que usará o MinioStorage)
            perfil.foto = arquivo
            
            # Debug: verificar a URL gerada após salvar
            print(f"URL do arquivo após salvar: {perfil.foto.url if perfil.foto else 'Nenhuma URL'}")
        
        # Processar senha
        nova_senha = request.POST.get('nova_senha')
        if nova_senha:
            usuario.set_password(nova_senha)
        
        # Salvar alterações
        usuario.save()
        perfil.save()
        
        messages.success(request, 'Perfil atualizado com sucesso!')
        
        # Após salvar, redirecionar para a URL de retorno
        return redirect(back_url)
    
    return render(request, 'perfil.html', {'usuario': usuario, 'back_url': back_url})

def home_view(request):
    """
    View para a página inicial do site.
    Redireciona para o dashboard apropriado se o usuário estiver autenticado,
    caso contrário, mostra a página inicial genérica.
    """
    if request.user.is_authenticated:
        # Redireciona para o portal adequado com base no nível do usuário
        if request.user.nivel in ['admin', 'gestor']:
            return redirect('gestor:dashboard')
        elif request.user.nivel == 'cliente':
            return redirect('cliente:dashboard')
        elif request.user.nivel == 'projetista':
            return redirect('projetista:dashboard')
        else:
            # Nível de usuário não reconhecido, redireciona para a página inicial padrão
            return render(request, 'home.html')
    else:
        # Usuário não autenticado, mostra a página inicial padrão
        return render(request, 'home.html')
    
def logout_view(request):
    """
    View para realizar o logout do usuário.
    """
    # Obter o contexto antes de fazer logout
    app_context = request.session.get('app_context', 'home')
    
    # Realizar o logout
    logout(request)
    
    # Mensagem de sucesso
    messages.success(request, 'Você foi desconectado com sucesso.')
    
    # Redirecionar com base no contexto
    if app_context == 'gestor':
        return redirect('gestor:login')
    elif app_context == 'cliente':
        return redirect('cliente:login')
    elif app_context == 'projetista':
        return redirect('projetista:login')
    else:
        return redirect('home')

class GestorLoginView(LoginView):
    template_name = 'gestor/login.html'
    
    def form_valid(self, form):
        print("Login bem-sucedido para:", form.get_user())
        return super().form_valid(form)
    
    def get_success_url(self):
        print("Redirecionando para:", reverse_lazy('gestor:dashboard'))
        return reverse_lazy('gestor:dashboard')
 
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['app_name'] = 'Portal do Gestor'
        return context


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