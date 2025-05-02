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