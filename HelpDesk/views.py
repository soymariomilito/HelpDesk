from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from .models import Ticket, Comentario
from .forms import TicketForm, FiltroForm, ComentarioForm, SolucionForm, UserRegistrationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import authenticate, login

# Create your views here.

#Muestra los tickets existentes
@login_required
def ticket_list(request):
    form = FiltroForm(request.GET)
    sort_param = request.GET.get('sort', 'id')  # Por defecto ordena por ID
    order = request.GET.get('order', 'desc')  # Por defecto ordena en orden descendente

     # Construir el campo de orden
    sort_field = f"{'-' if order == 'desc' else ''}{sort_param}"

    if request.user.is_staff:
        tickets = Ticket.objects.all().order_by(sort_field)

    else:
        tickets = Ticket.objects.filter(creado_por=request.user).order_by(sort_field)

    # Obtener los valores de los filtros desde la URL
    if form.is_valid():
        titulo = form.cleaned_data.get('titulo')
        ubicacion = form.cleaned_data.get('ubicacion')
        estado = form.cleaned_data.get('estado')
        prioridad = form.cleaned_data.get('prioridad')
        responsable = form.cleaned_data.get('responsable')

    # Filtrar los tickets según los valores obtenidos
    if titulo:
        tickets = tickets.filter(asunto__icontains=titulo)
    if ubicacion:
        tickets = tickets.filter(ubicacion=ubicacion)
    if estado:
        tickets = tickets.filter(estado=estado)
    if prioridad:
        tickets = tickets.filter(prioridad=prioridad)
    if responsable:
        if responsable == "0":
            tickets = tickets.filter(responsable__isnull=True)
        else:
            tickets = tickets.filter(responsable_id=responsable)

    # Aplicar paginación
    paginador = Paginator(tickets, 10)
    paginas = request.GET.get('page')
    pagina_actual = paginador.get_page(paginas)

    # Pasar los choices al contexto
    contexto = {
        'pagina_actual': pagina_actual,
        'form': form,
        'sort_param': sort_param,
        'order': order
    }

    return render(request, 'tickets/ticket_list.html', contexto)

#Abre otra interfaz para ver los detalles del ticket seleccionado
@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    comentarios = ticket.comentarios.all().order_by('-fecha_comentario')
    #ticket= Tickets.objects.get(pk=pk)

    #formulario de comeentarios
    if request.method == 'POST':
        comentario_form = ComentarioForm(request.POST)
        if comentario_form.is_valid():
            comentario = comentario_form.save(commit=False)
            comentario.ticket = ticket
            comentario.usuario = request.user
            comentario.save()

            # Enviar correo al solicitante
            html_message = render_to_string('emails/new_comment.html', {'ticket': ticket})
            plain_message = strip_tags(html_message)
            send_mail(
                subject=f"Nuevo comentario: {ticket.asunto}",
                message=plain_message,
                from_email='sistemas@47-street.com.ar',  
                recipient_list=[ticket.email_solicitante,'sistemas@47-street.com.ar'],
                html_message=html_message,
            )

            return redirect('ticket_detail', pk=ticket.pk)
    else:
        comentario_form = ComentarioForm()

    contexto = {
        'ticket': ticket,
        'comentarios': comentarios,
        'comentario_form': comentario_form
    }
    
    return render(request, 'tickets/ticket_detail.html', contexto)

#Creacion de nuevo ticket
@login_required
def new_ticket(request):
    if request.method == 'POST':
        form = TicketForm(request.POST, user=request.user)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.creado_por = request.user
            ticket.save()

            # Enviar correo al solicitante
            html_message = render_to_string('emails/ticket_creado.html', {'ticket': ticket})
            plain_message = strip_tags(html_message)
            send_mail(
                subject=f"Solicitud recibida: {ticket.asunto}",
                message=plain_message,
                from_email='sistemas@47-street.com.ar',  
                recipient_list=[ticket.email_solicitante,'sistemas@47-street.com.ar'],
                html_message=html_message,
                fail_silently=False,
            )

            return redirect('ticket_list')  # Redirige a la vista de lista de tickets después de crear uno
    else:
        form = TicketForm(user=request.user)

    return render(request, 'tickets/new_ticket.html', {'form': form})

@login_required
def tomar_ticket(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    # En caso de que el ticket ya este tomado tira un mensaje
    if ticket.responsable is not None and ticket.responsable != request.user:
        messages.error(request, "Este ticket ya ha sido asignado a otro usuario.")
        return redirect('ticket_detail', pk=pk)
    
    # Actualizar responsable y estado
    ticket.responsable = request.user
    ticket.estado = 'EN'
    ticket.save()

    comentario = Comentario(
            ticket=ticket,
            usuario=request.user,
            texto=f"Ha tomado el caso."
        )
    
    comentario.save()

    # Enviar correo al solicitante
    html_message = render_to_string('emails/tomar_caso.html', {'ticket': ticket})
    plain_message = strip_tags(html_message)
    send_mail(
        subject=f"Actualizacion: {ticket.asunto}",
        message=plain_message,
        from_email='sistemas@47-street.com.ar',  
        recipient_list=[ticket.email_solicitante],
        html_message=html_message,
    )

    messages.success(request, "Has tomado el caso!!")
    return redirect('ticket_detail', pk=pk)

@login_required
def esperenado_tercero(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    ticket.estado = 'ES'
    ticket.save()

    comentario = Comentario(
            ticket=ticket,
            usuario=request.user,
            texto=f"Ha cambiado el estado a 'Esperando 3ro'."
        )
    
    comentario.save()

    messages.success(request, "Has modificado el estado del caso")
    
    
    return redirect('ticket_detail', pk=pk)

@login_required
def cerrar_ticket(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    if request.method == 'POST':
        solucion = request.POST.get('solucion', '')
        if not solucion:
            messages.error(request, "Debe proporcionar una solución antes de cerrar el caso.")
            return redirect('ticket_detail', pk=ticket.pk)
        
        # Actualizar el ticket con la solución y cerrarlo
        ticket.solucion = solucion
        ticket.estado = 'CE'
        ticket.save()

    ticket.estado = 'CE'
    ticket.save()

    comentario = Comentario(
            ticket=ticket,
            usuario=request.user,
            texto=f"Ha cerrado el caso."
        )
    
    comentario.save()

    # Enviar correo al solicitante
    html_message = render_to_string('emails/cerrar_caso.html', {'ticket': ticket})
    plain_message = strip_tags(html_message)
    send_mail(
        subject=f"Actualizacion: {ticket.asunto}",
        message=plain_message,
        from_email='sistemas@47-street.com.ar',  
        recipient_list=[ticket.email_solicitante],
        html_message=html_message,
    )
    
    messages.success(request, "Has modificado el estado del caso")
   
    return redirect('ticket_detail', pk=pk)

@login_required
def reabrir_ticket(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    
    ticket.estado = 'EN' 
    ticket.responsable = None 
    ticket.save()
    
    comentario = Comentario(
            ticket=ticket,
            usuario=request.user,
            texto=f"Ha reabierto el caso."
        )
    comentario.save()

    messages.success(request, "Has modificado el estado del caso")
    
    return redirect('ticket_detail', pk=pk)

@login_required
def en_atencion(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    ticket.estado = 'EN'
    ticket.save()

    comentario = Comentario(
            ticket=ticket,
            usuario=request.user,
            texto=f"Ha cambiado el estado a 'En atención'."
        )
    
    comentario.save()

    messages.success(request, "Has modificado el estado del caso")
    
    
    return redirect('ticket_detail', pk=pk)

@login_required
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Desactivar la cuenta hasta que se confirme
            user.set_password(form.cleaned_data['password'])
            user.save()

            # Enviar correo de confirmación
            current_site = get_current_site(request)
            html_message = render_to_string('emails/confirm_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            plain_message = strip_tags(html_message)
            send_mail(
                subject= 'Confirma tu cuenta en HelpDesk',
                message= plain_message, 
                from_email='sistemas@47-street.com.ar',
                recipient_list=[user.email],
                html_message=html_message,
            )

            return render(request, 'registration/register_success.html', {'email': user.email})
    else:
        form = UserRegistrationForm()

    return render(request, 'registration/register.html', {'form': form})

def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Tu cuenta ha sido activada. Ya puedes iniciar sesión.')
        return redirect('login')
    else:
        messages.error(request, 'El enlace de activación no es válido.')
        return redirect('login')
    
def custom_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        try:
            user = User.objects.get(username=username)
            if not user.is_active:
                messages.error(request, 'Tu cuenta no está activa. Por favor confirma tu correo.')
                return render(request, 'registration/login.html', {'form': request.POST})
        except User.DoesNotExist:
            messages.error(request, 'El usuario no existe. Por favor regístrate.')
            return render(request, 'registration/login.html', {'form': request.POST})

        # Solo autenticar usuarios activos
        user = authenticate(request, username=username, password=password)
        print("Autenticación:", user)  # Verificar en los logs

        if user is not None:
            login(request, user)
            return redirect('ticket_list')
        else:
            messages.error(request, 'Credenciales inválidas. Intenta nuevamente.')

    return render(request, 'registration/login.html', {'form': request.POST})