from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from .models import Ticket, Comentario, Ubicacion, GrupoPersonalizado, ArchivoAdjunto
from .forms import TicketForm, FiltroForm, ComentarioForm, UserRegistrationForm, UbicacionForm, GrupoForm, UsuarioForm, ArchivoAdjuntoForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
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
from .utils import enviar_correo_ticket
import logging

# Create your views here.

logger = logging.getLogger('HelpDesk') 

#Muestra los tickets existentes
@login_required
def ticket_list(request):
    form = FiltroForm(request.GET)
    sort_param = request.GET.get('sort', 'id')  # Por defecto ordena por ID
    order = request.GET.get('order', 'desc')  # Por defecto ordena en orden descendente

     # Construir el campo de orden
    sort_field = f"{'-' if order == 'desc' else ''}{sort_param}"

    # Obtener el parámetro para filtrar por grupo.
    # Si no se selecciona grupo, se espera el valor "false"
    ver_grupo_param = request.GET.get("ver_grupo", "false")

    # Obtener los tickets según el rol del usuario
    if request.user.is_staff:
        tickets = Ticket.objects.all().order_by(sort_field)  # Admin ve todos los tickets
    else:
        tickets = Ticket.objects.filter(creado_por=request.user).order_by(sort_field)

        if ver_grupo_param != "false":
            try:
                grupo_id = int(ver_grupo_param)
                # Verificar que el usuario pertenezca a ese grupo
                grupo = GrupoPersonalizado.objects.get(id=grupo_id, usuarios=request.user)
                # Obtener todos los usuarios de ese grupo
                usuarios_grupo = User.objects.filter(grupos=grupo).distinct()
                tickets = Ticket.objects.filter(creado_por__in=usuarios_grupo).order_by(sort_field)
            except (ValueError, GrupoPersonalizado.DoesNotExist):
                # Si no se puede convertir a entero o el grupo no existe para el usuario, se ignora
                pass

        # Si el usuario es supervisora de una ubicación, también ve los tickets de su ubicación
        ubicaciones_supervisadas = Ubicacion.objects.filter(supervisora=request.user)
        if ubicaciones_supervisadas.exists():
            tickets = tickets | Ticket.objects.filter(ubicacion__in=ubicaciones_supervisadas).order_by(sort_field)

        # Si el usuario es el predeterminado de alguna ubicación, mostrar los tickets de esa ubicación
        ubicaciones_predeterminadas = Ubicacion.objects.filter(usuario_predeterminado=request.user, activo=True)
        if ubicaciones_predeterminadas.exists():
            tickets = tickets | Ticket.objects.filter(ubicacion__in=ubicaciones_predeterminadas).order_by(sort_field)


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
        'order': order,
        'ver_grupo': ver_grupo_param,
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

            # Registrar comentario
            logger.info(f"Nuevo comentario en ticket ID{ticket.id} por {request.user.username}")

            # Enviar correo al solicitante
            enviar_correo_ticket(ticket, 'emails/new_comment.html', f"Nuevo comentario: {ticket.asunto}")

            # Registrar Enví de mail
            logger.info(f"Se envió actualizacion por correo")

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
        form = TicketForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.creado_por = request.user
            ticket.save()

            archivos = request.FILES.getlist('archivos_adjuntos')
            for archivo in archivos:
                ArchivoAdjunto.objects.create(ticket=ticket, archivo=archivo)

            # Registrar la creación del ticket, envío de correo, etc.
            logger.info(f"Nuevo ticket creado por {request.user.username}: {ticket.asunto}")
            enviar_correo_ticket(ticket, 'emails/ticket_creado.html', f"{ticket.asunto}")
            logger.info(f"Se envió actualizacion por correo")

            return redirect('ticket_list')
    else:
        form = TicketForm(user=request.user)

    return render(request, 'tickets/new_ticket.html', {'form': form})

@require_POST
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

    # Registrar usuario que toma el caso
    logger.info(f"El ticket {ticket.id} ha sido tomado por {request.user.username}")

    comentario = Comentario(
            ticket=ticket,
            usuario=request.user,
            texto=f"Ha tomado el caso."
        )
    
    comentario.save()

    # Enviar correo al solicitante
    enviar_correo_ticket(ticket, 'emails/tomar_caso.html', f"Actualización: {ticket.asunto}")

    # Registrar Envió de mail
    logger.info(f"Se envió actualizacion por correo")

    messages.success(request, "Has tomado el caso!!")
    return redirect('ticket_detail', pk=pk)

@require_POST
@login_required
def esperando_tercero(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    ticket.estado = 'ES'
    ticket.save()

    comentario = Comentario(
            ticket=ticket,
            usuario=request.user,
            texto=f"Ha cambiado el estado a 'Esperando 3ro'."
        )
    
    comentario.save()

    # Registrar cambio de estado
    logger.info(f"El estado del ticket ID{ticket.id} ha sido cambiado a 'Esperando 3ro' por {request.user.username}")

    messages.success(request, "Has modificado el estado del caso")
    
    
    return redirect('ticket_detail', pk=pk)

@require_POST
@login_required
def cerrar_ticket(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    if request.method == 'POST':
        solucion = request.POST.get('solucion', '')
        # Actualizar el ticket con la solución y cerrarlo
        ticket.solucion = solucion
        ticket.estado = 'CE'
        ticket.save()
        if not solucion:
            messages.error(request, "Debe proporcionar una solución antes de cerrar el caso.")
            return redirect('ticket_detail', pk=ticket.pk)

    ticket.estado = 'CE'
    ticket.save()

    comentario = Comentario(
            ticket=ticket,
            usuario=request.user,
            texto=f"Ha cerrado el caso."
        )
    
    comentario.save()

    # Registrar cambio de estado
    logger.info(f"El ticket ID{ticket.id} ha sido cerrado por {request.user.username}")

    # Enviar correo al solicitante
    enviar_correo_ticket(ticket, 'emails/cerrar_caso.html', f"Actualización: {ticket.asunto}")

    # Registrar Envió de mail
    logger.info(f"Se envió actualizacion por correo")
    
    messages.success(request, "Has modificado el estado del caso")
   
    return redirect('ticket_detail', pk=pk)

@require_POST
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

@require_POST
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

@login_required
def lista_ubicaciones(request):
    if not request.user.is_staff:
        return redirect('ticket_list')

    ubicaciones = Ubicacion.objects.all()
    return render(request, 'ubicaciones/lista_ubicaciones.html', {'ubicaciones': ubicaciones})


@login_required
def nueva_ubicacion(request):
    if not request.user.is_staff:
        return redirect('ticket_list')

    if request.method == 'POST':
        form = UbicacionForm(request.POST)
        if form.is_valid():
            form.save()

            print(form)

            # Registrar creacion de ubicación 
            logger.info(f"Ubicación creada por {request.user.username}")

            return redirect('lista_ubicaciones')
    else:
        form = UbicacionForm()

    return render(request, 'ubicaciones/nueva_ubicacion.html', {'form': form})


@login_required
def editar_ubicacion(request, pk):
    if not request.user.is_staff:
        return redirect('ticket_list')

    ubicacion = get_object_or_404(Ubicacion, pk=pk)

    if request.method == 'POST':
        form = UbicacionForm(request.POST, instance=ubicacion)
        if form.is_valid():
            form.save()
            messages.success(request, "Ubicación actualizada correctamente.")

            # Registrar creacion de ubicación 
            logger.info(f"Ubicación {ubicacion} editada por {request.user.username}")

            return redirect('lista_ubicaciones')
    else:
        form = UbicacionForm(instance=ubicacion)

    return render(request, 'ubicaciones/editar_ubicacion.html', {'form': form})

@login_required
def lista_grupos(request):
    if not request.user.is_staff:
        return redirect('ticket_list')

    grupos = GrupoPersonalizado.objects.all()
    return render(request, 'grupos/lista_grupos.html', {'grupos': grupos})

@login_required
def nuevo_grupo(request):
    if not request.user.is_staff:
        return redirect('ticket_list')

    if request.method == 'POST':
        form = GrupoForm(request.POST)
        if form.is_valid():
            form.save()

            # Registrar creacion de grupo
            logger.info(f"Grupo creado por {request.user.username}")

            return redirect('lista_grupos')
    else:
        form = GrupoForm()

    return render(request, 'grupos/nuevo_grupo.html', {'form': form})

@login_required
def editar_grupo(request, pk):
    if not request.user.is_staff:
        return redirect('ticket_list')

    grupo = get_object_or_404(GrupoPersonalizado, pk=pk)

    if request.method == 'POST':
        form = GrupoForm(request.POST, instance=grupo)
        if form.is_valid():
            form.save()

            # Registrar creacion de grupo
            logger.info(f"Grupo {grupo} editado por {request.user.username}")

            return redirect('lista_grupos')
    else:
        form = GrupoForm(instance=grupo)

    return render(request, 'grupos/editar_grupo.html', {'form': form, 'grupo':grupo})

@login_required
def eliminar_grupo(request, pk):
    if not request.user.is_staff:
        return redirect('ticket_list')

    grupo = get_object_or_404(GrupoPersonalizado, pk=pk)
    grupo.delete()
    
    # Registrar creacion de grupo
    logger.info(f"Grupo eliminado por {request.user.username}")
    
    messages.success(request, "Grupo eliminado correctamente.")
    return redirect('lista_grupos')

@login_required
def lista_usuarios(request):
    if not request.user.is_staff:
        return redirect('ticket_list')

    usuarios = User.objects.all()
    return render(request, 'usuarios/lista_usuarios.html', {'usuarios': usuarios})

@login_required
def editar_usuario(request, pk):
    if not request.user.is_staff:
        return redirect('ticket_list')

    usuario = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()

            # Registrar edición de usuarios 
            logger.info(f"Usuario editado por {request.user.username}")

            return redirect('lista_usuarios')
    else:
        form = UsuarioForm(instance=usuario)

    return render(request, 'usuarios/editar_usuario.html', {'form': form, 'usuario': usuario})

@login_required
def eliminar_usuario(request, pk):
    if not request.user.is_staff:
        return redirect('ticket_list')

    usuario = get_object_or_404(User, pk=pk)
    usuario.delete()
    
    # Registrar edición de usuarios 
    logger.info(f"Usuario eliminado por {request.user.username}")
    
    return redirect('lista_usuarios')


@login_required
def add_attachment(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if request.method == 'POST':
        form = ArchivoAdjuntoForm(request.POST, request.FILES)
        if form.is_valid():
            archivos = request.FILES.getlist('archivos')
            for archivo in archivos:
                ArchivoAdjunto.objects.create(ticket=ticket, archivo=archivo)
            messages.success(request, "Archivos adjuntos agregados correctamente.")
            return redirect('ticket_detail', pk=ticket.pk)
    else:
        form = ArchivoAdjuntoForm()
    return render(request, 'tickets/add_attachment.html', {'form': form, 'ticket': ticket})
