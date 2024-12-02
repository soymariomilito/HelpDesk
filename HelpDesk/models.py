from django.db import models
from django.contrib.auth.models import User

# Create your models here.
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

    UBICACION_CHOICES = [
        ('Central', 'Central'),
        ('Pacifico', 'Pacifico'),
        ('Tortugas', 'Tortugas'),
        ('Aldrey', 'Aldrey'),
        ('Avellaneda', 'Avellaneda'),
        ('Alcorta', 'Alcorta'),
        ('Solar', 'Solar'),
        ('Village', 'Village'),
        ('DOT', 'DOT'),
        ('Nordelta', 'Nordelta'),
        ('Palermo', 'Palermo'),
        ('Unicenter', 'Unicenter'),
        ('47Abasto', 'Abasto'),
        ('47Soleil', 'Soleil'),
        ('47Arcos', 'Arcos'),
        ('47Flores', 'Flores'),
        ('47Florida', 'Florida'),
        ('47Soho', 'Soho'),
        ('47Salta', 'Salta'),
        ('47Palmas', 'Palmas'),
        ('47Pinamar', 'Pinamar'),
        ('47Lomitas', 'Lomitas'),
        ('MichDot', 'MichDot'),
    ]

    id = models.AutoField(primary_key=True)
    asunto = models.CharField(max_length=200)
    descripcion = models.TextField()
    estado = models.CharField(max_length=2, choices=ESTADO_CHOICES, default='AB')
    prioridad = models.CharField(max_length=2, choices=PRIORIDAD_CHOICES, default='BA')
    responsable = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, default=None)
    ubicacion = models.CharField(max_length=20, choices=UBICACION_CHOICES)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_creados')

    def __str__(self):
        return f"{self.asunto} ({self.get_estado_display()})"
    
class Comentario(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comentarios')
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    texto = models.TextField()
    fecha_comentario = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comentario de {self.usuario} en {self.ticket}"
    

 

