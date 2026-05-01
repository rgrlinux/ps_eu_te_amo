from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from .models import Perfil, Destinatario, Mensagem, LogAtividade

def verificar_inatividade():
    """Verifica usuários que não dão sinal de vida"""
    limite = timezone.now() - timedelta(days=30)
    perfis_suspeitos = Perfil.objects.filter(
        ultimo_sinal_vida__lt=limite,
        status='ativo'
    )

    resultados = []
    for perfil in perfis_suspeitos:
        # Calcular dias sem resposta
        dias_sem_resposta = (timezone.now() - perfil.ultimo_sinal_vida).days

        if dias_sem_resposta <= perfil.tempo_resposta_dias:
            continue

        # Já passou do prazo
        if dias_sem_resposta > perfil.tempo_resposta_dias + perfil.dias_tolerancia:
            # Tempo de tolerância esgotado - ativar curador
            perfil.status = 'suspeito'
            perfil.save()
            notificar_curador(perfil)
            resultados.append(f"Curador notificado para {perfil.usuario.email}")
        else:
            # Ainda em tolerância - enviar lembretes
            enviar_lembrete(perfil)
            resultados.append(f"Lembrete enviado para {perfil.usuario.email}")

    return resultados

def enviar_lembrete(perfil):
    """Envia lembrete para usuário"""
    assunto = "PS Eu Te Amo - Você está bem?"
    mensagem = f"""
    Olá {perfil.usuario.get_full_name()},

    Faz tempo que não recebemos um sinal seu. Por favor, confirme que está tudo bem:

    {gerar_link_confirmacao(perfil)}

    Se você não responder em {perfil.dias_tolerancia} dias,
    seu curador digital será notificado.

    Com amor,
    Equipe PS Eu Te Amo
    """

    send_mail(assunto, mensagem, 'nao-responda@pseteamo.com', [perfil.usuario.email])

    LogAtividade.objects.create(
        perfil=perfil,
        acao='lembrete_vida',
        detalhes=f"Lembrete enviado para {perfil.usuario.email}"
    )

def notificar_curador(perfil):
    """Notifica curador para confirmar falecimento"""
    assunto = f"URGENTE: Confirmar falecimento de {perfil.usuario.get_full_name()}"
    mensagem = f"""
    Olá {perfil.curador_nome},

    Não temos notícias de {perfil.usuario.get_full_name()} há mais de {perfil.tempo_resposta_dias} dias.

    Por favor, confirme se essa pessoa faleceu para que possamos enviar as mensagens póstumas.

    Link para confirmar falecimento:
    https://pseteamo.com/confirmar/{perfil.curador_codigo}

    Se a pessoa ainda está viva, ignore este e-mail.

    Atenciosamente,
    Equipe PS Eu Te Amo
    """

    send_mail(assunto, mensagem, 'nao-responda@pseteamo.com', [perfil.curador_email])

def confirmar_falecimento(codigo_curador):
    """Curador confirma falecimento e dispara mensagens"""
    try:
        perfil = Perfil.objects.get(curador_codigo=codigo_curador)
        perfil.status = 'falecido'
        perfil.save()

        # Disparar mensagens em ordem
        disparar_mensagens_postumas(perfil)

        LogAtividade.objects.create(
            perfil=perfil,
            acao='falecimento_confirmado',
            detalhes=f"Falecimento confirmado pelo curador {perfil.curador_email}"
        )

        return True
    except Perfil.DoesNotExist:
        return False

def disparar_mensagens_postumas(perfil):
    """Envia todas as mensagens para os destinatários"""
    destinatarios = perfil.destinatarios.all().order_by('ordem_envio')

    for dest in destinatarios:
        mensagens = dest.mensagens.filter(enviada=False)

        for msg in mensagens:
            # Aqui integra com serviço de email/SMS/WhatsApp
            enviar_mensagem_para_destinatario(dest, msg)

            msg.enviada = True
            msg.data_envio = timezone.now()
            msg.save()

    perfil.status = 'enviado'
    perfil.save()

def enviar_mensagem_para_destinatario(destinatario, mensagem):
    """Envia a mensagem específica para o destinatário"""
    assunto = f"Mensagem especial de {destinatario.perfil.usuario.get_full_name()}"
    corpo = f"""
    Olá {destinatario.nome},

    Esta é uma mensagem especial de {destinatario.perfil.usuario.get_full_name()}.

    {mensagem.conteudo}

    ---
    Esta mensagem foi enviada automaticamente pelo sistema PS Eu Te Amo.
    """

    if destinatario.tipo == 'email':
        send_mail(assunto, corpo, 'mensagens@pseteamo.com', [destinatario.contato])

    # TODO: Implementar WhatsApp, SMS, etc.

    LogAtividade.objects.create(
        perfil=destinatario.perfil,
        acao='mensagem_enviada',
        detalhes=f"Mensagem '{mensagem.titulo}' enviada para {destinatario.contato}"
    )

def gerar_link_confirmacao(perfil):
    """Gera link para usuário confirmar que está vivo"""
    from django.urls import reverse
    # Em produção, usar token JWT ou similar
    return f"https://pseteamo.com/confirmar-vida/{perfil.usuario.id}"

def sinal_vida(usuario_id):
    """Usuário confirma que está vivo"""
    try:
        perfil = Perfil.objects.get(usuario_id=usuario_id)
        perfil.ultimo_sinal_vida = timezone.now()
        perfil.status = 'ativo'
        perfil.save()

        LogAtividade.objects.create(
            perfil=perfil,
            acao='sinal_vida',
            detalhes="Usuário confirmou que está vivo"
        )

        return True
    except Perfil.DoesNotExist:
        return False
