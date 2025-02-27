from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.models import User

def enviar_correo_ticket(ticket, template, asunto):
    """
    Envía un correo a los destinatarios relevantes cuando hay cambios en un ticket.
    - Se envía siempre a "sistemas@47-street.com.ar".
    - Se envía al solicitante si existe.
    - Se envía al usuario predeterminado de la ubicación si no es el solicitante.
    - Se envía a la supervisora de la ubicación si existe.
    """

    destinatarios = {'sistemas@47-street.com.ar'}  # Usamos un `set` para evitar duplicados
    if ticket.email_solicitante:
        destinatarios.add(ticket.email_solicitante)

    usuario_solicitante = User.objects.filter(email=ticket.email_solicitante).first()
    if usuario_solicitante:
        for grupo in usuario_solicitante.grupos.all():
            for miembro in grupo.usuarios.all():
                if miembro.email and miembro.email != ticket.email_solicitante:
                    destinatarios.add(miembro.email)

    if ticket.ubicacion:
        if ticket.ubicacion.usuario_predeterminado and ticket.ubicacion.usuario_predeterminado.email:
            destinatarios.add(ticket.ubicacion.usuario_predeterminado.email)
        
        if ticket.ubicacion.supervisora and ticket.ubicacion.supervisora.email:
            destinatarios.add(ticket.ubicacion.supervisora.email)

    # Convertir el set en lista para enviarlo a send_mail
    destinatarios = list(destinatarios)
    print(destinatarios)
    # Generar el cuerpo del correo
    html_message = render_to_string(template, {'ticket': ticket})
    plain_message = strip_tags(html_message)

    # Enviar correo
    #send_mail(
    #    subject=asunto,
    #    message=plain_message,
    #    from_email='sistemas@47-street.com.ar',
    #    recipient_list=destinatarios,
    #    html_message=html_message,
    #    fail_silently=True
    #)
