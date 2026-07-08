from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.files.base import ContentFile
from PIL import Image
import hashlib

import io
class Perfil(models.Model):
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('suspeito', 'Suspeito (sem resposta)'),
        ('falecido', 'Falecido - aguardando envio'),
        ('enviado', 'Mensagens enviadas'),
    ]

    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
  # Corrigido: trocado 'anecdotes' por 'verbose_name'
    foto = models.ImageField(verbose_name='Foto de perfil', upload_to='avatar/%Y/%m/', blank=True, null=True)
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
        if self.arquivo:
            # 1. Calcular o hash lendo diretamente da memória
            self.arquivo.seek(0)
            self.hash_arquivo = hashlib.sha256(self.arquivo.read()).hexdigest()
            self.arquivo.seek(0)

            # 2. Processamento se for imagem
            if self.tipo == 'imagem':
                # Abrimos a imagem a partir do arquivo em memória (NÃO usamos .path)
                img = Image.open(self.arquivo)
                self.largura, self.altura = img.size

                # Redimensionar para max 1200px se necessário
                if max(self.largura, self.altura) > 1200:
                    img.thumbnail((1200, 1200), Image.LANCZOS)

                    # Atualiza largura/altura pós-redimensionamento
                    self.largura, self.altura = img.size

                    # Salva a imagem redimensionada em um buffer de memória
                    buffer = io.BytesIO()
                    img.save(buffer, format=img.format or 'JPEG', quality=85, optimize=True)
                    buffer.seek(0)

                    # Substitui o arquivo original pelo arquivo redimensionado em memória
                    # Isso garante que o Django salve o arquivo modificado no disco depois
                    novo_conteudo = ContentFile(buffer.read())
                    self.arquivo.save(self.arquivo.name, novo_conteudo, save=False)

                # Atualiza o tamanho em bytes usando a propriedade da instância na memória
                self.tamanho_bytes = self.arquivo.size
            else:
                # Se não for imagem (ex: documento), apenas pega o tamanho original
                self.tamanho_bytes = self.arquivo.size

        super().save(*args, **kwargs)

class LogAtividade(models.Model):
    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE)
    acao = models.CharField(max_length=100)
    detalhes = models.TextField(blank=True)
    ip = models.GenericIPAddressField(null=True)
    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.perfil.usuario.username} - {self.acao} - {self.data}"


class ServicoExtra(models.Model):
    # Seguindo o padrão de nomes das entidades em inglês para manter o padrão do projeto
    title = models.CharField(max_length=100, verbose_name="Nome do Serviço")
    description = models.TextField(verbose_name="Descrição")
    price = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Preço")
    emoji = models.CharField(max_length=10, default="⭐", verbose_name="Ícone/Emoji")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Serviço Extra"
        verbose_name = "Serviços Extras"

    def __str__(self):
        return self.title
