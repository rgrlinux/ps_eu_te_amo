from django import forms
from .models import Perfil, Destinatario, Mensagem

class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['tempo_resposta_dias', 'dias_tolerancia', 'curador_nome', 'curador_email', 'curador_telefone']
        labels = {
            'tempo_resposta_dias': 'Tempo sem resposta (dias)',
            'dias_tolerancia': 'Dias de tolerância antes de notificar curador',
            'curador_nome': 'Nome do curador (quem confirma seu falecimento)',
            'curador_email': 'E-mail do curador',
            'curador_telefone': 'Telefone do curador',
        }
        widgets = {
            'tempo_resposta_dias': forms.NumberInput(attrs={'class': 'form-control', 'min': 7, 'max': 365}),
            'dias_tolerancia': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 30}),
            'curador_nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Maria Silva'}),
            'curador_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'curador@email.com'}),
            'curador_telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(11) 99999-9999'}),
        }
        help_texts = {
            'tempo_resposta_dias': 'Após quantos dias sem resposta o sistema deve começar a alertar?',
            'dias_tolerancia': 'Após o alerta inicial, quantos dias até notificar o curador?',
            'curador_email': 'Essa pessoa receberá um e-mail para confirmar seu falecimento',
        }

class DestinatarioForm(forms.ModelForm):
    class Meta:
        model = Destinatario
        fields = ['nome', 'tipo', 'contato', 'ordem_envio']
        labels = {
            'nome': 'Nome completo',
            'tipo': 'Como receberá a mensagem',
            'contato': 'E-mail ou telefone',
            'ordem_envio': 'Ordem de envio (1 = primeiro)',
        }
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da pessoa amada'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'contato': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'email@exemplo.com ou (11) 99999-9999'}),
            'ordem_envio': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

class MensagemForm(forms.ModelForm):
    class Meta:
        model = Mensagem
        fields = ['titulo', 'conteudo']
        labels = {
            'titulo': 'Título da mensagem',
            'conteudo': 'Sua mensagem',
        }
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Para sempre no meu coração'}),
            'conteudo': forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Escreva aqui sua mensagem... Querida, se você está lendo isso...'}),
        }
