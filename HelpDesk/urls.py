from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import ticket_list, ticket_detail, new_ticket, tomar_ticket, cerrar_ticket, esperando_tercero, reabrir_ticket, en_atencion, register, activate_account,custom_login_view, lista_ubicaciones, editar_ubicacion, nueva_ubicacion, nuevo_grupo, editar_grupo, lista_grupos, eliminar_grupo, editar_usuario, lista_usuarios, eliminar_usuario, add_attachment

urlpatterns = [
    path('', ticket_list, name='ticket_list'),
    path('ticket_detail/<int:pk>/', ticket_detail, name='ticket_detail'),
    path('new_ticket/', new_ticket, name='new_ticket'),
    path('ticket/<int:pk>/take/', tomar_ticket, name='tomar_ticket'),
    path('ticket/<int:pk>/cerrar/', cerrar_ticket, name='cerrar_ticket'),
    path('ticket/<int:pk>/esperando/', esperando_tercero, name='esperando'),
    path('ticket/<int:pk>/reabrir/', reabrir_ticket, name='reabrir_ticket'),
    path('ticket/<int:pk>/atencion/', en_atencion, name='atencion'),
    path('register/', register, name='register'),
    path('activate/<uidb64>/<token>/', activate_account, name='activate_account'),
    path('login/', custom_login_view, name='login'), 
    path('ubicaciones/', lista_ubicaciones, name='lista_ubicaciones'),
    path('ubicaciones/nueva/', nueva_ubicacion, name='nueva_ubicacion'),
    path('ubicaciones/editar/<int:pk>/', editar_ubicacion, name='editar_ubicacion'),
    path('grupos/', lista_grupos, name='lista_grupos'),
    path('grupos/nuevo/', nuevo_grupo, name='nuevo_grupo'),
    path('grupos/editar/<int:pk>/', editar_grupo, name='editar_grupo'),
    path('grupos/eliminar/<int:pk>/', eliminar_grupo, name='eliminar_grupo'),
    path('usuarios/', lista_usuarios, name='lista_usuarios'),
    path('usuarios/editar/<int:pk>/', editar_usuario, name='editar_usuario'),
    path('usuarios/eliminar/<int:pk>/', eliminar_usuario, name='eliminar_usuario'),
    path('tickets/<int:pk>/add_attachment/', add_attachment, name='add_attachment'),
]

if settings.DEBUG:  # Solo en desarrollo
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)