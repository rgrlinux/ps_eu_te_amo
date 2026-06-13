from django.urls import path
from django.contrib.auth import views as auth_views
from . import views, view_checkout

urlpatterns = [
    path('', views.index, name='index'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('configurar-perfil/', views.configurar_perfil, name='configurar_perfil'),
    path('destinatario/novo/', views.criar_destinatario, name='criar_destinatario'),
    path('mensagem/novo/<int:destinatario_id>/', views.criar_mensagem, name='criar_mensagem'),
    path('confirmar-vida/<int:usuario_id>/', views.confirmar_vida, name='confirmar_vida'),
    path('confirmar-falecimento/<str:codigo>/', views.confirmar_falecimento_view, name='confirmar_falecimento'),
    path('renovar/', views.renovar_assinatura, name='renovar_assinatura'),
    path('criar-checkout/', view_checkout.create_checkout, name='criar_checkout'),
    path('mensagens/', views.listar_mensagens, name='listar_mensagens'),
    path('servicos/', views.listar_servicos, name='listar_servicos'),
]
