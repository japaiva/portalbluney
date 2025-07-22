# portalcomercial/urls.py - URLs PRINCIPAIS ATUALIZADAS

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from core.views import PortalLoginView, home_view, logout_view, perfil

def redirect_after_login(request):
    """View para redirecionar usuários baseado no nível - FALLBACK"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    user = request.user
    
    if user.is_superuser:
        return redirect('/gestor/')
    elif hasattr(user, 'nivel'):
        if user.nivel == 'admin':
            return redirect('/gestor/')
        elif user.nivel == 'gestor':
            return redirect('/gestor/')
        elif user.nivel == 'vendedor':
            return redirect('/vendedor/')
        else:
            return redirect('/vendedor/')
    else:
        # Fallback se não tem nível
        return redirect('/vendedor/')

urlpatterns = [
    # ===== ADMIN =====
    path('admin/', admin.site.urls),
    
    # ===== AUTHENTICATION =====
    path('login/', PortalLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    
    # ===== PERFIL (GLOBAL) =====
    path('perfil/', perfil, name='perfil'),
    
    # ===== HOME E REDIRECIONAMENTO =====
    path('', home_view, name='home'),
    path('dashboard/', login_required(redirect_after_login), name='dashboard'),
    
    # ===== MÓDULOS =====
    path('gestor/', include('gestor.urls')),
    path('vendedor/', include('vendedor.urls')),
    
    # ===== API =====
    path('api/', include('api.urls')),
]

# Servir arquivos de mídia durante desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)