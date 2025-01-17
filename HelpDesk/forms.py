from django import forms
from .models import Ticket, Comentario
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['asunto', 'descripcion', 'prioridad', 'ubicacion', 'email_solicitante']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Obtener el usuario
        super().__init__(*args, **kwargs)

        # Si el usuario no es staff, ocultar el campo y completarlo automáticamente
        if user and not user.is_staff:
            self.fields['email_solicitante'].widget = forms.HiddenInput()  # Ocultar el campo
            self.fields['email_solicitante'].initial = user.email  # Prellenar con el email del usuario

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

class SolucionForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['solucion']
        widgets = {
            'solucion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe la solución...'}),
        }

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email']
        if not email.endswith('@47-street.com.ar'):
            raise ValidationError("El email debe pertenecer al dominio @47-street.com.ar")
        if User.objects.filter(email=email).exists():
            raise ValidationError("Este email ya está registrado.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Las contraseñas no coinciden.")