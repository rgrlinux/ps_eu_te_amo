import stripe
from django.conf import settings
from django.shortcuts import redirect


stripe.api_key = settings.SECRET_STRIPE_API_KEY


if settings.DEBUG:
    url = 'http://localhost:8000'
else:
    url = 'https://ps_eu_te_amo.com.br'

def create_checkout(request):
    session = stripe.checkout.Session.create(
        payment_method_types=['card', 'pix'],
        mode='subscription',
        line_items=[{
            'price': 'price_1TT90CCc7ic2cadjH9ADeh3C',
            'quantity': 1,
        }],
        success_url=f'{url}/success',
        cancel_url=f'{url}/cancel',
    )
    return redirect(session.url)
