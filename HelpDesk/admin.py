from django.contrib import admin
from .models import Ticket, Comentario, Ubicacion, GrupoPersonalizado

# Register your models here.
admin.site.register(Ticket)
admin.site.register(Comentario)
admin.site.register(Ubicacion)
admin.site.register(GrupoPersonalizado)