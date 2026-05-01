from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
# from django.utils import
from .models import Perfil, Destinatario,  Midia
from .tasks import sinal_vida, confirmar_falecimento
from .forms import PerfilForm, DestinatarioForm, MensagemForm
import hashlib

def index(request):
    return render(request, 'core/index.html')

def cadastro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Perfil.objects.create(usuario=user)
            login(request, user)
            messages.success(request, 'Cadastro realizado! Complete seu perfil.')
            return redirect('configurar_perfil')
    else:
        form = UserCreationForm()
    return render(request, 'core/cadastro.html', {'form': form})

@login_required
def configurar_perfil(request):
    perfil, created = Perfil.objects.get_or_create(usuario=request.user)

    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil configurado com sucesso!')
            return redirect('dashboard')
    else:
        form = PerfilForm(instance=perfil)

    return render(request, 'core/configurar_perfil.html', {'form': form})

@login_required
def dashboard(request):
    perfil = request.user.perfil
    destinatarios = perfil.destinatarios.all()
    total_mensagens = sum(d.mensagens.count() for d in destinatarios)

    # Atualizar sinal de vida
    sinal_vida(request.user.id)

    # Calcular dias restantes
    from .views_utils import calcular_dias_restantes
    dias_restantes = calcular_dias_restantes(perfil)

    context = {
        'perfil': perfil,
        'destinatarios': destinatarios,
        'total_mensagens': total_mensagens,
        'dias_restantes': dias_restantes,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def criar_destinatario(request):
    if request.method == 'POST':
        form = DestinatarioForm(request.POST)
        if form.is_valid():
            destinatario = form.save(commit=False)
            destinatario.perfil = request.user.perfil
            destinatario.save()
            messages.success(request, f'Destinatário {destinatario.nome} adicionado!')
            return redirect('dashboard')
    else:
        form = DestinatarioForm()

    return render(request, 'core/destinatario_form.html', {'form': form})

@login_required
def criar_mensagem(request, destinatario_id):
    destinatario = get_object_or_404(Destinatario, id=destinatario_id, perfil__usuario=request.user)

    if request.method == 'POST':
        form = MensagemForm(request.POST)
        if form.is_valid():
            mensagem = form.save(commit=False)
            mensagem.destinatario = destinatario
            mensagem.save()

            # Processar mídias enviadas
            arquivos = request.FILES.getlist('arquivos')
            for arquivo in arquivos:
                # Calcular hash
                hash_md5 = hashlib.md5()
                for chunk in arquivo.chunks():
                    hash_md5.update(chunk)

                Midia.objects.create(
                    mensagem=mensagem,
                    arquivo=arquivo,
                    tipo='imagem' if arquivo.content_type.startswith('image') else 'documento',
                    tamanho_bytes=arquivo.size,
                    hash_arquivo=hash_md5.hexdigest()
                )

            messages.success(request, 'Mensagem criada com sucesso!')
            return redirect('dashboard')
    else:
        form = MensagemForm()

    return render(request, 'core/mensagem_form.html', {'form': form, 'destinatario': destinatario})

def confirmar_vida(request, usuario_id):
    if sinal_vida(usuario_id):
        messages.success(request, 'Obrigado por confirmar! Estamos felizes que você está bem 💚')
    else:
        messages.error(request, 'Erro ao confirmar. Tente novamente.')
    return redirect('index')

def confirmar_falecimento_view(request, codigo):
    if confirmar_falecimento(codigo):
        return render(request, 'core/confirmado.html', {'sucesso': True})
    return render(request, 'core/confirmado.html', {'sucesso': False})

@login_required
def renovar_assinatura(request):
    return render(request, 'core/renovacao.html')
