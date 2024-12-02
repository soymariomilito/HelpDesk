from django import forms
from .models import Ticket, Comentario
from django.contrib.auth.models import User

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['asunto', 'descripcion', 'prioridad', 'ubicacion']

class FiltroForm(forms.Form):
    titulo = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': 'buscar por titulo',
        'class': 'form-control mr-2'
    }))

    estado = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos los estados')] + Ticket.ESTADO_CHOICES, widget=forms.Select(attrs={'class': 'form-control mr-2'})
    )
    
    prioridad = forms.ChoiceField(
        required=False,
        choices=[('', 'Todas las prioridades')] + Ticket.PRIORIDAD_CHOICES, widget=forms.Select(attrs={'class': 'form-control mr-2'})
    )

    ubicacion = forms.ChoiceField(
        required=False,
        choices=[('', 'Todas las ubicaciones')] + Ticket.UBICACION_CHOICES, widget=forms.Select(attrs={'class': 'form-control mr-2'})
    )

    responsable = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos los responsables'), ('0', 'Sin asignar')], widget=forms.Select(attrs={'class': 'form-control mr-2'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['responsable'].choices += [
            (user.id, user.username) for user in User.objects.all()
        ]
    
class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ['texto']
        widgets = {
            'texto': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Agregar un comentario...'})
        }
