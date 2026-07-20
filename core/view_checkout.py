from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import stripe

stripe.api_key = settings.SECRET_STRIPE_API_KEY

# Define a URL base dinamicamente
BASE_URL = 'http://localhost:8000' if settings.DEBUG else 'https://ps_eu_te_amo.com.br'

@login_required
@require_POST
def create_checkout(request):
    # Recupera o tipo de plano enviado pelo HTML
    plan_type = request.POST.get('plan_type')

    # Dicionário mapeando o tipo do plano para o Price ID gerado lá no painel do Stripe
    # Substitua pelas strings reais 'price_...' que o Stripe gerou para você
    PLAN_PRICE_IDS = {
        'basic': 'price_1Tv4NXCc7ic2cadjkqkHG2Mt',   # ID do preço de R$ 49/ano
        'premium': 'price_1Tv4WFCc7ic2cadjZxZ9L0GK', # ID do preço de R$ 129/ano
    }

    stripe_price_id = PLAN_PRICE_IDS.get(plan_type)

    # Se alguém tentar mandar um plano inválido ou o grátis por POST, manda de volta
    if not stripe_price_id:
        return redirect('planos_page')

    try:
        checkout_session = stripe.checkout.Session.create(
            client_reference_id=request.user.id, # Passa o ID do usuário logado
            payment_method_types=['card'],       # Ative 'pix' aqui se já configurou no painel
            line_items=[
                {
                    'price': stripe_price_id,
                    'quantity': 1,
                },
            ],
            mode='subscription', # Modo assinatura para pagamentos recorrentes
            success_url=request.build_absolute_uri('/success/'), # Suas rotas criadas
            cancel_url=request.build_absolute_uri('/cancel/'),
        )
        # Redireciona o usuário direto para o checkout seguro do Stripe
        return redirect(checkout_session.url, status=303)

    except Exception as e:
        # Em caso de erro, você pode logar ou tratar de outra forma
        return HttpResponse(f"Erro ao criar sessão de checkout: {str(e)}", status=500)

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

    # Lidando com os eventos da Assinatura
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        # Recuperamos o ID do usuário que colocamos no 'client_reference_id'
        user_id = session.get('client_reference_id')
        subscription_id = session.get('subscription') # ID da assinatura criada

        if user_id:
            # TODO: Aqui você busca seu User no banco e ativa a assinatura dele!
            # Exemplo:
            # profile = UserProfile.objects.get(user_id=user_id)
            # profile.is_premium = True
            # profile.stripe_subscription_id = subscription_id
            # profile.save()
            print(f"Usuário {user_id} assinou com sucesso! ID: {subscription_id}")

    elif event['type'] == 'invoice.payment_failed':
        # Disparado se o pagamento de alguma parcela mensal falhar
        invoice = event['data']['object']
        subscription_id = invoice.get('subscription')
        # TODO: Bloquear o acesso do usuário à plataforma até ele regularizar
        print(f"Pagamento falhou para a assinatura {subscription_id}")

    elif event['type'] == 'customer.subscription.deleted':
        # Disparado se o usuário cancelar a assinatura ou se ela expirar
        subscription = event['data']['object']
        subscription_id = subscription.get('id')
        # TODO: Desativar a conta premium no seu banco de dados
        print(f"Assinatura cancelada: {subscription_id}")

    return HttpResponse(status=200)
