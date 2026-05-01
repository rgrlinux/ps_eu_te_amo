from django.utils import timezone

def calcular_dias_restantes(perfil):
    """Calcula quantos dias faltam para o próximo sinal de vida"""
    ultimo_sinal = perfil.ultimo_sinal_vida
    prazo = ultimo_sinal + timezone.timedelta(days=perfil.tempo_resposta_dias)
    restante = (prazo - timezone.now()).days
    return max(0, restante)
