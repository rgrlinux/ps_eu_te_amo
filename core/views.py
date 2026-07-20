import stripe
from ps_eu_te_amo import settings
from django.utils.timezone import make_aware
from datetime import datetime
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login,logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
# from django.utils import
from .models import Perfil,Midia, Mensagem, ServicoExtra, Destinatario
from .tasks import sinal_vida, confirmar_falecimento
from .forms import PerfilForm, DestinatarioForm, MensagemForm
import hashlib

import logging

logger = logging.getLogger(__name__)


def index(request):
    return render(request, 'core/index.html')

class editar_mensagem(LoginRequiredMixin, View):
    """
    View para renderizar e salvar o formulário de edição de uma mensagem.
    """
    def get(self, request, pk):
        # Obtém a mensagem pelo ID
        mensagem = get_object_or_404(Mensagem, pk=pk)

        # Instancia o Form com os dados da mensagem atual
        form = MensagemForm(instance=mensagem)

        return render(request, 'core/editar_mensagem.html', {
            'form': form,
            'mensagem': mensagem
        })

    def post(self, request, pk):
        mensagem = get_object_or_404(Mensagem, pk=pk)
        form = MensagemForm(request.POST, request.FILES or None, instance=mensagem)

        if form.is_valid():
            form.save()
            messages.success(request, "Mensagem atualizada com sucesso!")
            # Redireciona de volta para o dashboard principal
            return redirect('dashboard')  # Substitua pelo nome correto da sua URL do dashboard

        return render(request, 'dashboard/editar_mensagem.html', {
            'form': form,
            'mensagem': mensagem
        })

class editar_destinatario(LoginRequiredMixin, View):
    """
    View para atualizar os dados de um destinatário (nome, email, telefone, etc).
    """
    def get(self, request, pk):
        destinatario = get_object_or_404(Destinatario, pk=pk, perfil__usuario=request.user)
        form = DestinatarioForm(instance=destinatario)
        return render(request, 'core/editar_destinatario.html', {'form': form, 'destinatario': destinatario})

    def post(self, request, pk):
        destinatario = get_object_or_404(Destinatario, pk=pk, perfil__usuario=request.user)
        form = DestinatarioForm(request.POST, instance=destinatario)

        if form.is_valid():
            form.save()
            messages.success(request, "Destinatário atualizado com sucesso!")
            return redirect('dashboard')  # Redireciona para o dashboard ou outra página

        return render(request, 'core/editar_destinatario.html', {'form': form, 'destinatario': destinatario})

# views.py
def cadastro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                Perfil.objects.create(usuario=user)
                login(request, user)
                messages.success(request, 'Cadastro realizado! Complete seu perfil.')
                return redirect('configurar_perfil')
            except Exception as e:
                messages.error(request, f'Erro no cadastro: {e}')
    else:
        form = UserCreationForm()
    return render(request, 'core/cadastro.html', {'form': form})

# views.py
@login_required
def configurar_perfil(request):
    # Garantir que o perfil existe
    perfil, created = Perfil.objects.get_or_create(usuario=request.user)

    if created:
        messages.info(request, 'Perfil criado automaticamente. Configure seus dados.')

    if request.method == 'POST':
        form = PerfilForm(request.POST, request.FILES, instance=perfil)
        if form.is_valid():

            user = request.user
            user.first_name = form.cleaned_data.get('first_name', user.first_name)
            user.last_name = form.cleaned_data.get('last_name', user.last_name)
            user.email = form.cleaned_data.get('email', user.email)
            user.save()
            form.save()
            messages.success(request, 'Perfil configurado com sucesso!')
            return redirect('dashboard')
    else:
        form = PerfilForm(instance=perfil)

    return render(request, 'core/configurar_perfil.html', {
            'form': form,
            'perfil': perfil
        })

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
def criar_mensagem(request):
    if request.method == 'POST':
        form = MensagemForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            mensagem = form.save(commit=False)
            mensagem.save()

            # Processar mídias enviadas
            arquivos = request.FILES.getlist('arquivos')
            for arquivo in arquivos:
                # Calcular hash
                hash_md5 = hashlib.md5()
                for chunk in arquivo.chunks():
                    hash_md5.update(chunk)

                arquivo.seek(0)

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
        form = MensagemForm(user=request.user)

    return render(request, 'core/mensagem_form.html', {'form': form})

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


@login_required
def listar_mensagens(request):
    perfil = request.user.perfil
    # Filtra as mensagens cujos destinatários pertencem ao perfil do usuário logado
    mensagens = Mensagem.objects.filter(destinatario__perfil=perfil).order_by('-data_criacao')

    context = {
        'perfil': perfil,
        'mensagens': mensagens,
    }
# Verifica se a requisição foi feita via JavaScript (Fetch/AJAX)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Renderiza APENAS o HTML da tabela isolada
        return render(request, 'core/partials/tabela_mensagens_fragmento.html', context)

    # Se o usuário acessar a URL direto pelo navegador, carrega a página completa antiga
    return render(request, 'core/listar_mensagens_completo.html', context)


    # return render(request, 'core/mensagens_lista.html', context)


@login_required
def listar_servicos(request):
    perfil = request.user.perfil
    servicos = ServicoExtra.objects.filter(is_active=True)

    context = {
        'perfil': perfil,
        'servicos': servicos,
    }

    # Se a requisição veio do script JS do Dashboard, manda só o miolo
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'core/partials/servicos_fragmento.html', context)

    # Caso acesse direto pela URL, mantém o comportamento antigo de carregar tudo
    return render(request, 'core/servicos_lista.html', context)


@login_required
def logout_view(request):
    logout(request)
    # messages.success(request, 'Você saiu com sucesso!')
    return redirect('index')  # Ou 'login' se tiver página de login

@login_required
def criar_mensagem_completa(request):
    if request.method == 'POST':
        form_destinatario = DestinatarioForm(request.POST)
        form_mensagem = MensagemForm(request.POST)

        # Valida os dois formulários ao mesmo tempo
        if form_destinatario.is_valid() and form_mensagem.is_valid():
            # 1. Salva o Destinatário primeiro
            destinatario = form_destinatario.save(commit=False)
            destinatario.perfil = request.user.perfil
            destinatario.save()

            # 2. Salva a Mensagem vinculando ao destinatário recém-criado
            mensagem = form_mensagem.save(commit=False)
            mensagem.destinatario = destinatario
            mensagem.save()

            # 3. Processa os arquivos/mídias (igual ao seu código anterior)
            arquivos = request.FILES.getlist('arquivos')
            for arquivo in arquivos:
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

            messages.success(request, 'Mensagem e destinatário criados com sucesso!')
            return redirect('dashboard')
    else:
        # Se for GET, exibe ambos os formulários vazios
        form_destinatario = DestinatarioForm()
        form_mensagem = MensagemForm()

    context = {
        'form_destinatario': form_destinatario,
        'form_mensagem': form_mensagem
    }
    return render(request, 'core/mensagem_form.html', context)

def carregar_tabela_destinatarios(request):
    # Pega todos os destinatários do usuário logado
    destinatarios_lista = Mensagem.objects.filter(destinatario__perfil=request.user.perfil).order_by('destinatario','-data_criacao')
    # destinatarios_lista = Destinatario.objects.filter(perfil=request.user.perfil).order_by('ordem_envio', 'id') # ajuste o filtro

    # Paginação: exibe 5 destinatários por página, por exemplo
    paginator = Paginator(destinatarios_lista, 5)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'core/partials/tabela_destinatarios.html', {'page_obj': page_obj})

    return redirect('dashboard')

def payment_success(request):
    # Dica: O Stripe pode enviar o ?session_id= na URL se você configurou na success_url
    return HttpResponse("""
        <html>
            <head><link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css"></head>
            <body class="container" style="margin-top: 10vh; max-width: 600px;">
                <article style="border-color: green;">
                    <header>✅ Pagamento Recebido!</header>
                    <p>Muito obrigado! Sua assinatura está sendo processada. Você já pode acessar a plataforma.</p>
                    <a href="/dashboard/" class="button">Ir para o Dashboard</a>
                </article>
            </body>
        </html>
    """)

def payment_cancel(request):
    return HttpResponse("""
        <html>
            <head><link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css"></head>
            <body class="container" style="margin-top: 10vh; max-width: 600px;">
                <article style="border-color: red;">
                    <header>❌ Operação Cancelada</header>
                    <p>O processo de pagamento foi interrompido. Nenhuma cobrança foi realizada.</p>
                    <a href="/renovar/" class="button secondary">Tentar Novamente</a>
                </article>
            </body>
        </html>
    """)


# O Stripe envia Webhooks sem o token CSRF do Django, por isso usamos @csrf_exempt
@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    # Pegue esta chave no painel do Stripe (Developers > Webhooks) ou no Stripe CLI
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        # Payload inválido
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        # Assinatura digital inválida
        return HttpResponse(status=400)

    event_type = event['type']
    data_object = event['data']['object']

    # 1. Checkout concluído (Primeiro pagamento com sucesso)
    if event_type == 'checkout.session.completed':
        user_id = data_object.get('client_reference_id')
        stripe_customer_id = data_object.get('customer')
        stripe_subscription_id = data_object.get('subscription')

        if user_id:
            try:
                perfil = Perfil.objects.get(usuario_id=user_id)
                perfil.stripe_customer_id = stripe_customer_id
                perfil.stripe_subscription_id = stripe_subscription_id

                # Defina a lógica do plano comprado (ex: vindo de metadados ou fixo se tiver só um pago)
                perfil.plano = 'premium'
                perfil.data_assinatura = make_aware(datetime.now())
                perfil.save()
                logger.info(f"Plano Premium ativado para o perfil do usuário {user_id}")
            except Perfil.DoesNotExist:
                logger.error(f"Perfil do usuário {user_id} não foi encontrado.")

    # 2. Assinatura atualizada/renovada (Muda data de expiração ou plano)
    elif event_type == 'customer.subscription.updated':
        stripe_subscription_id = data_object.get('id')
        stripe_status = data_object.get('status') # 'active', 'past_due', 'unpaid'

        current_period_end = data_object.get('current_period_end')
        data_expiracao = make_aware(datetime.fromtimestamp(current_period_end))

        try:
            perfil = Perfil.objects.get(stripe_subscription_id=stripe_subscription_id)
            perfil.data_expiracao = data_expiracao

            # Se o pagamento falhar ou atrasar, você pode rebaixar o plano ou tratar aqui
            if stripe_status != 'active':
                perfil.plano = 'gratuito' # Ou uma lógica customizada de bloqueio temporário

            perfil.save()
            logger.info(f"Inscrição {stripe_subscription_id} atualizada. Expira em: {data_expiracao}")
        except Perfil.DoesNotExist:
            logger.error(f"Assinatura Stripe {stripe_subscription_id} não mapeada em nenhum Perfil.")

    # 3. Assinatura cancelada definitivamente
    elif event_type == 'customer.subscription.deleted':
        stripe_subscription_id = data_object.get('id')

        try:
            perfil = Perfil.objects.get(stripe_subscription_id=stripe_subscription_id)
            perfil.plano = 'gratuito'
            perfil.data_expiracao = make_aware(datetime.now()) # Expira imediatamente
            perfil.save()
            logger.info(f"Assinatura {stripe_subscription_id} cancelada. Perfil retornou ao plano gratuito.")
        except Perfil.DoesNotExist:
            pass

    return HttpResponse(status=200)
