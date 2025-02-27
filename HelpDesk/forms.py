from django import forms
from .models import Ticket, Comentario, Ubicacion, GrupoPersonalizado
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class TicketForm(forms.ModelForm):
    archivos_adjuntos = forms.FileField(
        required=False, 
        widget=forms.ClearableFileInput(attrs={'allow_multiple_selected': True}),
        label="Archivos Adjuntos"
    )

    class Meta:
        model = Ticket
        fields = ['asunto', 'descripcion', 'prioridad', 'ubicacion', 'email_solicitante', 'archivos_adjuntos']
        labels = {
            'descripcion': 'Descripción',
            'ubicacion': 'Ubicación',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Obtener el usuario
        super().__init__(*args, **kwargs)

        # Filtrar ubicaciones activas
        self.fields['ubicacion'].queryset = Ubicacion.objects.filter(activo=True).order_by('nombre')

        # Si el usuario no es staff, ocultar el campo y completarlo automáticamente
        if user and not user.is_staff:
            self.fields['email_solicitante'].initial = user.email  # Prellenar con el email del usuario
            # Deshabilitar el campo para que no se pueda modificar
            self.fields['email_solicitante'].widget.attrs['disabled'] = True

        # Si el usuario es el predeterminado de alguna ubicación, se asigna esa ubicación
            default_ubicacion = Ubicacion.objects.filter(usuario_predeterminado=user, activo=True).first()
            if default_ubicacion:
                self.fields['ubicacion'].initial = default_ubicacion
                # Deshabilitar el campo para que no se pueda modificar
                self.fields['ubicacion'].widget.attrs['disabled'] = True

    def clean_ubicacion(self):
        """
        Si el campo está deshabilitado, devolvemos el valor inicial,
        ya que el valor no se envía en el POST.
        """
        if self.fields['ubicacion'].widget.attrs.get('disabled'):
            return self.fields['ubicacion'].initial
        return self.cleaned_data.get('ubicacion')
    
    def clean_email_solicitante(self):
        """
        Si el campo está deshabilitado, devolvemos el valor inicial,
        ya que el valor no se envía en el POST.
        """
        if self.fields['email_solicitante'].widget.attrs.get('disabled'):
            return self.fields['email_solicitante'].initial
        return self.cleaned_data.get('email_solicitante')

    def clean_archivo_adjunto(self):
        archivos = self.files.getlist('archivos_adjuntos')
        if archivos:
            # Limitar tamaño máximo (por ejemplo, 25 MB)
            max_tamaño = 25 * 1024 * 1024
            if archivos.size > max_tamaño:
                raise forms.ValidationError("El archivo no debe superar los 25 MB.")
        return archivos
    
class UbicacionForm(forms.ModelForm):
    class Meta:
        model = Ubicacion
        fields = ['nombre', 'activo', 'supervisora', 'usuario_predeterminado']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'supervisora': forms.Select(attrs={'class': 'form-control'}),
            'usuario_predeterminado': forms.Select(attrs={'class': 'form-control'}),
        }

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

    ubicacion = forms.ModelChoiceField(
        required=False,
        queryset=Ubicacion.objects.all().order_by('nombre'), 
        empty_label="Todas las ubicaciones",
        widget=forms.Select(attrs={'class': 'form-control mr-2'})
    )

    responsable = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos los responsables'), ('0', 'Sin asignar')], widget=forms.Select(attrs={'class': 'form-control mr-2'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['responsable'].choices += [
            (user.id, user.username) for user in User.objects.filter(is_staff=True)
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
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Nombre"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Contraseña"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirmar Contraseña"
    )

    class Meta:
        model = User
        fields = ['first_name', 'username', 'email', 'password']
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

    def save(self, commit=True):
        # Guardar el usuario con los datos del formulario
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])  # Encripta la contraseña
        if commit:
            user.save()
        return user

class GrupoForm(forms.ModelForm):
    usuarios = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget= forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = GrupoPersonalizado
        fields = ['nombre', 'usuarios']
        widgets ={
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
        }

class UsuarioForm(forms.ModelForm):
    is_staff = forms.BooleanField(required=False, label="Es staff")
    is_active = forms.BooleanField(required=False, label="Cuenta activa")

    class Meta:
        model = User
        fields = ['first_name', 'username', 'email', 'is_staff', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class ArchivoAdjuntoForm(forms.Form):
    archivos = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'allow_multiple_selected': True}),
        label="Agregar Archivos Adicionales"
    )