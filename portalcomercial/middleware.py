# portalcomercial/middleware.py
from django.db.models import Q

class MensagensNotificacaoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Injetar contagem de mensagens não lidas para usuários autenticados
        if request.user.is_authenticated:
            # Comentado temporariamente até implementarmos um sistema de mensagens
            # A implementação original era:
            # from projetos.models import Mensagem
            # mensagens_nao_lidas = Mensagem.objects.filter(
            #    Q(destinatario=request.user) | 
            #    (Q(projeto__criado_por=request.user) & ~Q(remetente=request.user)),
            #    lida=False
            # ).count()
            
            # Versão temporária - define como zero
            request.user.mensagens_nao_lidas = 0
        
        return response
    
class AppContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Detectar o contexto da aplicação com base na URL
        path = request.path
        
        # Determinar o contexto baseado no caminho da URL
        # Adaptado para os contextos do novo projeto
        if '/gestor/' in path:
            request.session['app_context'] = 'gestor'
        elif '/vendedor/' in path:
            request.session['app_context'] = 'vendedor'
        elif '/admin/' in path:
            request.session['app_context'] = 'admin'
        # Não alterar o contexto se não estiver em uma URL específica
        
        response = self.get_response(request)
        return response
    
class PermissaoPortalMiddleware:
    """
    Middleware para verificar permissões de acesso aos portais
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Verificar permissões apenas para usuários autenticados
        if request.user.is_authenticated:
            path = request.path
            
            # Se é superuser, permitir tudo
            if request.user.is_superuser:
                response = self.get_response(request)
                return response
            
            # Se não tem atributo nivel, permitir acesso (compatibilidade)
            if not hasattr(request.user, 'nivel'):
                response = self.get_response(request)
                return response
            
            user_nivel = request.user.nivel
            
            # Definir permissões por portal - AQUI ESTÁ A RESTRIÇÃO!
            portal_permissions = {
                '/gestor/': ['admin', 'gestor'],          # SÓ admin e gestor podem acessar
                '/vendedor/': ['admin', 'gestor', 'vendedor'],  # Vendedores podem acessar seu próprio módulo
                # Adicione outros portais conforme necessário
            }
            
            # Verificar se o usuário tem permissão para acessar o portal
            for portal_path, allowed_levels in portal_permissions.items():
                if path.startswith(portal_path):
                    if user_nivel not in allowed_levels:
                        from django.http import HttpResponseForbidden
                        from django.contrib import messages
                        from django.shortcuts import redirect
                        
                        # Opção 1: Retornar erro 403
                        # return HttpResponseForbidden(
                        #     f"Acesso negado. Seu nível ({user_nivel}) não tem permissão para acessar este portal."
                        # )
                        
                        # Opção 2: Redirecionar com mensagem (mais elegante)
                        messages.error(
                            request, 
                            f'Acesso negado ao módulo gestor! Seu nível ({request.user.get_nivel_display()}) não tem permissão.'
                        )
                        
                        # Redirecionar baseado no nível do usuário
                        if user_nivel == 'vendedor':
                            return redirect('/vendedor/')  # ou use reverse('vendedor:dashboard')
                        else:
                            return redirect('/')  # home
                    break
        
        response = self.get_response(request)
        return response