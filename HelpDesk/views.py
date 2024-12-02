from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from .models import Ticket, Comentario
from .forms import TicketForm, FiltroForm, ComentarioForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Create your views here.

#Muestra los tickets existentes
@login_required
def ticket_list(request):
    form = FiltroForm(request.GET)

    tickets = Ticket.objects.all().order_by('-id')

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
        'form': form
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
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.creado_por = request.user
            ticket.save()
            return redirect('ticket_list')  # Redirige a la vista de lista de tickets después de crear uno
    else:
        form = TicketForm()
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

    ticket.estado = 'CE'
    ticket.save()

    comentario = Comentario(
            ticket=ticket,
            usuario=request.user,
            texto=f"Ha cerrado el caso."
        )
    
    comentario.save()
    
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
