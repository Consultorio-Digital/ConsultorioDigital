# principal/views.py
from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.db.models import Q
from django.utils import timezone
from consultorio.models import Reserva, Profesional

def home(request: HttpRequest):
    if not request.user.is_authenticated:
        return redirect('login')

    if Profesional.objects.filter(usuario__rut=request.user.username).exists():
        return redirect('panel_doctor')

    reservas = []

    if request.user.is_authenticated:
        try:
            hoy = timezone.localdate()
            reservas = (
                Reserva.objects
                .filter(paciente__usuario__rut=request.user.username)
                .filter(
                    # Citas activas con fecha de hoy en adelante
                    Q(estado__in=['pendiente', 'confirmada'],
                      fecha_reserva__date__gte=hoy)
                    |
                    # Seguimientos con fecha de seguimiento pendiente
                    Q(estado='seguimiento',
                      fecha_seguimiento__gte=hoy)
                )
                .select_related('consultorio', 'profesional__usuario')
                .order_by('fecha_reserva')
            )
        except Exception:
            reservas = []

    confirmacion = request.session.pop('reserva_confirmada', None)

    return render(
        request=request,
        template_name="principal.html",
        context={
            "title"       : "Página principal",
            "reservas"    : reservas,
            "confirmacion": confirmacion,
        }
    )