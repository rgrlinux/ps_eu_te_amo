from django.conf import settings
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import stripe

stripe.api_key = settings.SECRET_STRIPE_API_KEY

# Define a URL base dinamicamente
BASE_URL = 'http://localhost:8000' if settings.DEBUG else 'https://ps_eu_te_amo.com.br'

@require_POST  # Garante que a criação só aconteça via POST
def create_checkout(request):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='subscription',
            line_items=[{
                'price': 'price_1TT90CCc7ic2cadjH9ADeh3C',
                'quantity': 1,
            }],
            # Adicionar o ID do usuário nos metadados ajuda a saber quem pagou no webhook!
            client_reference_id=request.user.id if request.user.is_authenticated else None,
            success_url=f'{BASE_URL}/success/',
            cancel_url=f'{BASE_URL}/cancel/',
        )
        return redirect(session.url, status=303)  # 303 é o recomendado para redirecionamentos pós-POST
    except stripe.error.StripeError as e:
        # Trate o erro de API aqui (ex: logar o erro ou renderizar uma página amigável)
        # return render(request, 'error.html', {'message': 'Não foi possível iniciar o pagamento.'})
        return HttpResponse(f"Erro no Stripe: {e}", status=400)


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
    except ValueError as e:
        # Payload inválido
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
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
