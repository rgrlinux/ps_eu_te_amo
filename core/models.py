from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from PIL import Image
import hashlib
import os

class Perfil(models.Model):
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('suspeito', 'Suspeito (sem resposta)'),
        ('falecido', 'Falecido - aguardando envio'),
        ('enviado', 'Mensagens enviadas'),
    ]

    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    ultimo_sinal_vida = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo')

    # Configurações
    tempo_resposta_dias = models.IntegerField(default=30)  # dias sem resposta
    dias_tolerancia = models.IntegerField(default=7)  # após falhar, avisos diários

    # Curador digital (quem confirma o falecimento)
    curador_nome = models.CharField(max_length=200, blank=True)
    curador_email = models.EmailField(blank=True)
    curador_telefone = models.CharField(max_length=20, blank=True)
    curador_codigo = models.CharField(max_length=64, blank=True, unique=True)

    # Assinatura
    plano = models.CharField(max_length=20, default='gratuito')  # gratuito, basico, premium
    data_assinatura = models.DateTimeField(null=True, blank=True)
    data_expiracao = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.curador_codigo:
            import secrets
            self.curador_codigo = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.usuario.username} - {self.status}"

class Destinatario(models.Model):
    TIPO_CHOICES = [
        ('email', 'E-mail'),
        ('whatsapp', 'WhatsApp'),
        ('telegram', 'Telegram'),
        ('sms', 'SMS'),
    ]

    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name='destinatarios')
    nome = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    contato = models.CharField(max_length=200)  # email ou telefone
    ordem_envio = models.IntegerField(default=1)  # ordem de envio

    def __str__(self):
        return f"{self.nome} ({self.tipo})"

class Mensagem(models.Model):
    destinatario = models.ForeignKey(Destinatario, on_delete=models.CASCADE, related_name='mensagens')
    titulo = models.CharField(max_length=200)
    conteudo = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_envio = models.DateTimeField(null=True, blank=True)
    enviada = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.titulo} - {self.destinatario.nome}"

class Midia(models.Model):
    mensagem = models.ForeignKey(Mensagem, on_delete=models.CASCADE, related_name='midias')
    arquivo = models.FileField(upload_to='midias/%Y/%m/')
    tipo = models.CharField(max_length=10)  # imagem, video, documento
    hash_arquivo = models.CharField(max_length=64, unique=True)
    tamanho_bytes = models.IntegerField()
    largura = models.IntegerField(null=True, blank=True)
    altura = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Calcular hash
        if self.arquivo:
            self.hash_arquivo = hashlib.sha256(self.arquivo.read()).hexdigest()
            self.arquivo.seek(0)

            # Redimensionar se for imagem
            if self.tipo == 'imagem':
                img = Image.open(self.arquivo.path)
                self.largura, self.altura = img.size

                # Redimensionar para max 1200px
                if max(self.largura, self.altura) > 1200:
                    img.thumbnail((1200, 1200), Image.LANCZOS)
                    img.save(self.arquivo.path, quality=85, optimize=True)

                # Atualizar tamanho
                self.tamanho_bytes = os.path.getsize(self.arquivo.path)

        super().save(*args, **kwargs)

class LogAtividade(models.Model):
    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE)
    acao = models.CharField(max_length=100)
    detalhes = models.TextField(blank=True)
    ip = models.GenericIPAddressField(null=True)
    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.perfil.usuario.username} - {self.acao} - {self.data}"
