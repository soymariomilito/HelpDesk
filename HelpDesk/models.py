from django.db import models
from django.contrib.auth.models import User

# Create your models here.

# Tabla de ubicaciones
class Ubicacion(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    activo = models.BooleanField(default=True)
    supervisora = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ubicaciones_supervisadas')
    usuario_predeterminado = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ubicaciones_asignadas')

    def __str__(self):
        return self.nombre
    
# Tabla de tickets
class Ticket(models.Model):
    ESTADO_CHOICES = [
        ('AB', 'Abierto'),
        ('EN', 'En atención'),
        ('ES', 'Esperando 3ro'),
        ('CE', 'Cerrado'),
    ]

    PRIORIDAD_CHOICES = [
        ('BA', 'Baja'),
        ('ME', 'Media'),
        ('AL', 'Alta'),
    ]

    id = models.AutoField(primary_key=True)
    asunto = models.CharField(max_length=200)
    descripcion = models.TextField()
    estado = models.CharField(max_length=2, choices=ESTADO_CHOICES, default='AB')
    prioridad = models.CharField(max_length=2, choices=PRIORIDAD_CHOICES, default='BA')
    responsable = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, default=None)
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.SET_NULL, null=True, blank=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_creados')
    email_solicitante = models.EmailField(max_length=254, null=True, blank=True, default=None)
    solucion = models.TextField(null=True, blank=True, default=None)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.asunto} ({self.get_estado_display()})"
    
# Tabla para archivos adjuntos
class ArchivoAdjunto(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='archivos_adjuntos')
    archivo = models.FileField(upload_to='tickets/')
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Archivo de {self.ticket.asunto}"

# Tabla de comentarios    
class Comentario(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comentarios')
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    texto = models.TextField()
    fecha_comentario = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comentario de {self.usuario} en {self.ticket}"

# Tabla de grupos
class GrupoPersonalizado(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    usuarios = models.ManyToManyField(User, related_name='grupos')
    
    def __str__(self):
        return self.nombre
    



