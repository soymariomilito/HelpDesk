from django.urls import path
from .views import ticket_list, ticket_detail, new_ticket, tomar_ticket, cerrar_ticket, esperenado_tercero, reabrir_ticket

urlpatterns = [
    path('', ticket_list, name='ticket_list'),
    path('ticket_detail/<int:pk>/', ticket_detail, name='ticket_detail'),
    path('new_ticket/', new_ticket, name='new_ticket'),
    path('ticket/<int:pk>/take/', tomar_ticket, name='tomar_ticket'),
    path('ticket/<int:pk>/cerrar/', cerrar_ticket, name='cerrar_ticket'),
    path('ticket/<int:pk>/esperando/', esperenado_tercero, name='esperando'),
    path('ticket/<int:pk>/reabrir/', reabrir_ticket, name='reabrir_ticket'),
]