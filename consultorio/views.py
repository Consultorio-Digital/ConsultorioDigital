from datetime import datetime, date, timedelta

from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Min
from django.utils import timezone

from .models import Consultorio, Reserva, Usuario, Paciente, Profesional, Disponibilidad

# ---------------------------------------------------------------------------
# NOTAS DE DESARROLLO — restricciones pendientes de producción
# ---------------------------------------------------------------------------
# 1. FECHAS EN EL PASADO: actualmente el flujo de reserva (paciente) y la
#    declaración de disponibilidad (doctor) permiten seleccionar fechas y
#    horarios pasados. Esto es intencional para facilitar pruebas.
#    En producción se deberá validar que fecha_reserva >= now() en la vista
#    `seleccionar_region` y que la fecha de disponibilidad >= hoy en
#    `panel_doctor` (action='disponibilidad').
#
# 2. CÓDIGO DE CANCELACIÓN: el código de 6 dígitos se genera y muestra
#    directamente en pantalla. En producción debería enviarse al correo
#    registrado del paciente y no mostrarse en la interfaz.
# ---------------------------------------------------------------------------


@login_required(login_url='/login/')
def seleccionar_region(request):
    if request.method == 'POST':
        consultorio_id = request.POST.get('consultorio')
        profesional_id = request.POST.get('profesional_id')
        motivo         = request.POST.get('motivo', '').strip()
        slot           = request.POST.get('slot')  # "YYYY-MM-DD HH:MM"

        if not motivo:
            return redirect('consultorio')

        try:
            fecha_reserva = datetime.strptime(slot, "%Y-%m-%d %H:%M")
            if timezone.is_naive(fecha_reserva):
                fecha_reserva = timezone.make_aware(fecha_reserva)

            u = request.user
            usuario, _ = Usuario.objects.get_or_create(
                rut=u.username,
                defaults={
                    'nombre'           : u.first_name or u.username,
                    'apellido'         : u.last_name or '',
                    'fecha_nacimiento' : date.today(),
                    'correo'           : u.email or '',
                },
            )
            paciente, _ = Paciente.objects.get_or_create(
                usuario=usuario,
                defaults={'ingreso': date.today()},
            )
            consultorio  = Consultorio.objects.get(objectid=consultorio_id)
            profesional  = Profesional.objects.select_related('usuario').get(id=profesional_id)

            # Verificar que el slot sigue disponible (evitar doble reserva)
            slot_tomado = Reserva.objects.filter(
                profesional=profesional,
                fecha_reserva=fecha_reserva,
            ).exclude(estado='cancelada').exists()

            if not slot_tomado:
                Reserva.objects.create(
                    consultorio=consultorio,
                    paciente=paciente,
                    profesional=profesional,
                    fecha_reserva=fecha_reserva,
                    motivo=motivo,
                )

            doctor_nombre = f"Dr/a. {profesional.usuario.nombre} {profesional.usuario.apellido}"
            request.session['reserva_confirmada'] = {
                'consultorio' : consultorio.nombre,
                'fecha'       : fecha_reserva.strftime("%d/%m/%Y"),
                'hora'        : fecha_reserva.strftime("%H:%M"),
                'doctor'      : doctor_nombre,
                'ya_tomado'   : slot_tomado,
            }
        except Exception as e:
            print(f"Error al crear reserva: {e}")

        return redirect('principal:principal')

    regiones = (
        Consultorio.objects
        .values('c_reg')
        .annotate(nom_reg=Min('nom_reg'))
        .filter(nom_reg__isnull=False)
        .exclude(nom_reg='')
        .order_by('c_reg')
    )
    return render(request, 'consultorio.html', {'regiones': regiones})


# ── Historial de citas de un paciente (para el doctor) ───────────────

@login_required(login_url='/login/')
def historial_paciente(request):
    """Devuelve JSON con datos de contacto y citas previas de un paciente,
    solo visibles para doctores. No incluye información clínica."""
    paciente_id    = request.GET.get('paciente_id')
    consultorio_id = request.GET.get('consultorio_id')

    # Solo doctores pueden consultar esto
    if not Profesional.objects.filter(usuario__rut=request.user.username).exists():
        return JsonResponse({'error': 'No autorizado'}, status=403)

    try:
        paciente = Paciente.objects.select_related('usuario').get(id=paciente_id)
    except Paciente.DoesNotExist:
        return JsonResponse({'error': 'Paciente no encontrado'}, status=404)

    u = paciente.usuario
    citas = (
        Reserva.objects
        .filter(paciente=paciente, consultorio_id=consultorio_id)
        .order_by('-fecha_reserva')
        .values(
            'id', 'fecha_reserva', 'motivo', 'estado',
            'notas_doctor', 'fecha_seguimiento',
        )
    )

    citas_lista = []
    for c in citas:
        citas_lista.append({
            'fecha'        : c['fecha_reserva'].strftime('%d/%m/%Y %H:%M'),
            'motivo'       : c['motivo'],
            'estado'       : c['estado'],
            'instruccion'  : c['notas_doctor'] or '',
            'seguimiento'  : c['fecha_seguimiento'].strftime('%d/%m/%Y') if c['fecha_seguimiento'] else '',
        })

    return JsonResponse({
        'nombre'   : f"{u.nombre} {u.apellido}",
        'rut'      : u.rut,
        'correo'   : u.correo,
        'telefono' : u.telefono or '',
        'citas'    : citas_lista,
    })


# ── Endpoints AJAX para el flujo de reserva ──────────────────────────

@login_required(login_url='/login/')
def obtener_doctores(request):
    """Doctores que trabajan en un consultorio dado."""
    consultorio_id = request.GET.get('consultorio_id')
    if not consultorio_id:
        return JsonResponse([], safe=False)

    doctores = (
        Profesional.objects
        .filter(consultorio_id=consultorio_id)
        .select_related('usuario')
        .order_by('usuario__apellido', 'usuario__nombre')
    )
    data = [
        {
            'id'          : d.id,
            'nombre'      : f"{d.usuario.nombre} {d.usuario.apellido}",
            'especialidad': d.especialidad,
        }
        for d in doctores
    ]
    return JsonResponse(data, safe=False)


@login_required(login_url='/login/')
def obtener_fechas(request):
    """Fechas con disponibilidad declarada para un profesional (hoy en adelante)."""
    profesional_id = request.GET.get('profesional_id')
    if not profesional_id:
        return JsonResponse([], safe=False)

    hoy    = timezone.localdate()
    fechas = (
        Disponibilidad.objects
        .filter(profesional_id=profesional_id, fecha__gte=hoy)
        .values_list('fecha', flat=True)
        .distinct()
        .order_by('fecha')
    )
    return JsonResponse([str(f) for f in fechas], safe=False)


@login_required(login_url='/login/')
def obtener_slots(request):
    """Slots de 30 min libres para un profesional en una fecha."""
    profesional_id = request.GET.get('profesional_id')
    fecha_str      = request.GET.get('fecha')

    if not profesional_id or not fecha_str:
        return JsonResponse([], safe=False)

    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse([], safe=False)

    disponibilidades = Disponibilidad.objects.filter(
        profesional_id=profesional_id,
        fecha=fecha,
    )

    # Generar todos los slots posibles (bloques de 30 min)
    all_slots = []
    for disp in disponibilidades:
        current = datetime.combine(fecha, disp.hora_inicio)
        end     = datetime.combine(fecha, disp.hora_fin)
        while current < end:
            all_slots.append(current)
            current += timedelta(minutes=30)

    # Slots ya ocupados
    taken_qs = (
        Reserva.objects
        .filter(profesional_id=profesional_id, fecha_reserva__date=fecha)
        .exclude(estado='cancelada')
        .values_list('fecha_reserva', flat=True)
    )
    taken_times = {timezone.localtime(dt).strftime("%H:%M") for dt in taken_qs}

    free = [
        {'value': s.strftime("%Y-%m-%d %H:%M"), 'label': s.strftime("%H:%M")}
        for s in all_slots
        if s.strftime("%H:%M") not in taken_times
    ]
    return JsonResponse(free, safe=False)

@login_required(login_url='/login/')
def obtener_comunas(request, c_reg):
    comunas = (
        Consultorio
        .objects
        .filter(c_reg=c_reg)
        .values('c_com', 'nom_com')
        .distinct()
        .order_by('nom_com')
    )
    return JsonResponse(list(comunas), safe=False)

@login_required(login_url='/login/')
def obtener_consultorios(request, c_com):
    consultorios = (
        Consultorio
        .objects
        .filter(c_com=c_com)
        .values()
    )
    return JsonResponse(list(consultorios), safe=False)

# Create your views here.
def home(request: HttpRequest):
    return render(
        request = request, 
        template_name = "consultorio.html", 
        context = {"title": "Página principal del consultorio"}
    )

@login_required(login_url='/login/')
def mis_horas(request: HttpRequest):
    from django.core.paginator import Paginator

    try:
        from django.db.models import Q
        hoy = timezone.localdate()
        # Historial: todo lo que NO está en "Próximas citas"
        qs = (
            Reserva.objects
            .filter(paciente__usuario__rut=request.user.username)
            .exclude(
                Q(estado__in=['pendiente', 'confirmada'],
                  fecha_reserva__date__gte=hoy)
                |
                Q(estado='seguimiento',
                  fecha_seguimiento__gte=hoy)
            )
            .select_related('consultorio', 'profesional__usuario')
            .order_by('-fecha_reserva')
        )
    except Exception:
        qs = Reserva.objects.none()

    paginator = Paginator(qs, 15)
    page_obj  = paginator.get_page(request.GET.get('page'))

    return render(
        request=request,
        template_name="mis_horas.html",
        context={"title": "Historial de citas", "page_obj": page_obj},
    )

@login_required(login_url='/login/')
def reservar_hora(request: HttpRequest):
    return render(
        request = request, 
        template_name = "reservar_hora.html", 
        context = {"title": "Reservar hora"}
    )

@login_required(login_url='/login/')
def cancelar_hora(request: HttpRequest):
    import random

    if request.method == 'POST':
        action = request.POST.get('action')

        # ── Paso 1: selección de cita → generar código y guardarlo en sesión ──
        if action == 'seleccionar':
            reserva_id = request.POST.get('reserva_id')
            if reserva_id:
                codigo = f"{random.randint(0, 999999):06d}"
                request.session['cancelacion'] = {
                    'reserva_id': reserva_id,
                    'codigo'    : codigo,
                }
            return redirect('cancelar_hora')

        # ── Limpiar sesión → volver al paso 1 ──
        if action == 'limpiar':
            request.session.pop('cancelacion', None)
            request.session.pop('codigo_incorrecto', None)
            return redirect('cancelar_hora')

        # ── Paso 2: verificar código → cancelar o rechazar ──
        if action == 'confirmar':
            cancelacion  = request.session.get('cancelacion', {})
            confirmar_id = request.POST.get('confirmar_reserva_id')
            codigo_input = request.POST.get('codigo', '').strip()
            motivo_can   = request.POST.get('motivo_cancelacion', '').strip()

            if (
                str(cancelacion.get('reserva_id')) == str(confirmar_id)
                and cancelacion.get('codigo') == codigo_input
            ):
                try:
                    reserva = Reserva.objects.get(
                        id=confirmar_id,
                        paciente__usuario__rut=request.user.username,
                    )
                    reserva.estado             = 'cancelada'
                    reserva.motivo_cancelacion = motivo_can or None
                    reserva.save()
                except Reserva.DoesNotExist:
                    pass
                request.session.pop('cancelacion', None)
                request.session['reserva_cancelada'] = True
                return redirect('principal:principal')
            else:
                # Código incorrecto: volver al paso 2 con error
                request.session['codigo_incorrecto'] = True
                return redirect('cancelar_hora')

    # ── GET: renderizar según estado de sesión ──
    cancelacion       = request.session.get('cancelacion')
    codigo_incorrecto = request.session.pop('codigo_incorrecto', False)

    try:
        reservas_activas = (
            Reserva.objects
            .filter(
                paciente__usuario__rut=request.user.username,
                estado__in=['pendiente', 'confirmada'],
            )
            .select_related('consultorio', 'profesional__usuario')
            .order_by('fecha_reserva')
        )
    except Exception:
        reservas_activas = []

    reserva_seleccionada = None
    codigo_generado      = None

    if cancelacion:
        rid = cancelacion.get('reserva_id')
        reserva_seleccionada = Reserva.objects.filter(
            id=rid,
            paciente__usuario__rut=request.user.username,
        ).select_related('consultorio', 'profesional__usuario').first()
        codigo_generado = cancelacion.get('codigo')

    return render(request, 'cancelar_hora.html', {
        'title'               : 'Cancelar hora',
        'reservas_activas'    : reservas_activas,
        'reserva_seleccionada': reserva_seleccionada,
        'codigo_generado'     : codigo_generado,
        'codigo_incorrecto'   : codigo_incorrecto,
    })

@login_required(login_url='/login/')
def panel_doctor(request):
    from .models import Disponibilidad

    hoy         = timezone.localdate()
    profesional = (
        Profesional.objects
        .filter(usuario__rut=request.user.username)
        .select_related('consultorio')
        .first()
    )

    if not profesional:
        return redirect('login')

    tab_activa = 'citas'

    # ── POST: guardar recinto ──────────────────────────────────────────
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'recinto':
            cid = request.POST.get('recinto')
            if cid:
                try:
                    profesional.consultorio = Consultorio.objects.get(objectid=cid)
                    profesional.save()
                except Consultorio.DoesNotExist:
                    pass
            tab_activa = 'disponibilidad'
            return redirect(f"{request.path}?tab=disponibilidad")

        elif action == 'disponibilidad':
            fecha       = request.POST.get('fecha')
            hora_inicio = request.POST.get('hora_inicio')
            hora_fin    = request.POST.get('hora_fin')
            if fecha and hora_inicio and hora_fin:
                Disponibilidad.objects.get_or_create(
                    profesional=profesional,
                    fecha=fecha,
                    hora_inicio=hora_inicio,
                    defaults={'hora_fin': hora_fin},
                )
            return redirect(f"{request.path}?tab=disponibilidad")

        elif action == 'eliminar_disponibilidad':
            disp_id = request.POST.get('disponibilidad_id')
            try:
                disp = Disponibilidad.objects.get(id=disp_id, profesional=profesional)
                # Verificar reservas activas dentro de ese bloque horario
                from datetime import datetime as dt
                inicio = timezone.make_aware(dt.combine(disp.fecha, disp.hora_inicio))
                fin    = timezone.make_aware(dt.combine(disp.fecha, disp.hora_fin))
                activas = Reserva.objects.filter(
                    profesional=profesional,
                    fecha_reserva__gte=inicio,
                    fecha_reserva__lt=fin,
                    estado__in=['pendiente', 'confirmada'],
                ).count()
                if activas:
                    request.session['error_disponibilidad'] = (
                        f"No puedes eliminar este bloque: tiene {activas} cita{'s' if activas > 1 else ''} "
                        f"activa{'s' if activas > 1 else ''} dentro del horario. "
                        f"Cancélalas primero o espera a que sean gestionadas."
                    )
                else:
                    disp.delete()
            except Disponibilidad.DoesNotExist:
                pass
            return redirect(f"{request.path}?tab=disponibilidades")

        elif action == 'no_asistio':
            reserva_id = request.POST.get('reserva_id')
            try:
                reserva = Reserva.objects.get(
                    id=reserva_id,
                    profesional=profesional,
                )
                reserva.estado = 'no_asistio'
                reserva.save()
            except Reserva.DoesNotExist:
                pass
            tab = request.POST.get('tab_activa', 'citas')
            return redirect(f"{request.path}?tab={tab}")

        elif action in ('confirmar', 'completar', 'seguimiento', 'reabrir'):
            reserva_id = request.POST.get('reserva_id')
            try:
                reserva = Reserva.objects.get(
                    id=reserva_id,
                    profesional=profesional,
                )
                if action == 'confirmar':
                    reserva.estado      = 'confirmada'
                    reserva.profesional = profesional
                elif action == 'completar':
                    reserva.estado       = 'completada'
                    notas = request.POST.get('notas_doctor', '').strip()
                    if notas:
                        reserva.notas_doctor = notas
                elif action == 'seguimiento':
                    fecha_seg = request.POST.get('fecha_seguimiento')
                    notas     = request.POST.get('notas_doctor', '').strip()
                    reserva.estado = 'seguimiento'
                    if fecha_seg:
                        reserva.fecha_seguimiento = fecha_seg
                    if notas:
                        reserva.notas_doctor = notas
                elif action == 'reabrir':
                    reserva.estado            = 'pendiente'
                    reserva.notas_doctor      = None
                    reserva.fecha_seguimiento = None
                reserva.save()
            except Reserva.DoesNotExist:
                pass
            tab = request.POST.get('tab_activa', 'citas')
            return redirect(f"{request.path}?tab={tab}")

    tab_activa           = request.GET.get('tab', 'citas')
    error_disponibilidad = request.session.pop('error_disponibilidad', None)

    # ── Queries según recinto asignado ────────────────────────────────
    reservas_hoy           = []
    reservas_pendientes    = []
    reservas_sin_gestionar = []
    disponibilidades       = []
    page_historial         = None
    disponibilidades_json  = '{}'
    total_hoy              = 0
    total_pendientes       = 0
    total_completadas      = 0
    total_sin_gestionar    = 0
    total_historial        = 0

    if profesional.consultorio:
        from django.db.models import ExpressionWrapper, BooleanField, Q as Qm
        ahora = timezone.now()
        reservas_hoy = (
            Reserva.objects
            .filter(
                profesional=profesional,
                fecha_reserva__date=hoy,
            )
            .exclude(estado='cancelada')
            .annotate(
                es_pasada=ExpressionWrapper(
                    Qm(fecha_reserva__lt=ahora),
                    output_field=BooleanField(),
                )
            )
            .select_related('paciente__usuario')
            .order_by('fecha_reserva')
        )
        total_hoy         = reservas_hoy.count()
        total_pendientes  = reservas_hoy.filter(estado='pendiente').count()
        total_completadas = reservas_hoy.filter(estado__in=['completada', 'seguimiento']).count()

        # Citas sin gestionar: datetime ya pasó (incluye hoy con hora vencida)
        ahora = timezone.now()
        reservas_sin_gestionar = (
            Reserva.objects
            .filter(
                profesional=profesional,
                fecha_reserva__lt=ahora,
                estado__in=['pendiente', 'confirmada'],
            )
            .select_related('paciente__usuario')
            .order_by('-fecha_reserva')
        )
        total_sin_gestionar = reservas_sin_gestionar.count()

        # Fechas con disponibilidad declarada (futuras)
        fechas_disp = (
            Disponibilidad.objects
            .filter(profesional=profesional, fecha__gt=hoy)
            .values_list('fecha', flat=True)
        )
        reservas_pendientes = (
            Reserva.objects
            .filter(
                profesional=profesional,
                fecha_reserva__date__in=fechas_disp,
            )
            .exclude(estado__in=['cancelada', 'completada', 'seguimiento', 'no_asistio'])
            .select_related('paciente__usuario')
            .order_by('fecha_reserva')
        )

        disponibilidades = (
            Disponibilidad.objects
            .filter(profesional=profesional)
            .select_related('profesional__consultorio')
            .order_by('fecha', 'hora_inicio')
        )

        # Serializar disponibilidades para el calendario JS
        import json
        disp_cal = {}
        for d in disponibilidades:
            key = str(d.fecha)
            if key not in disp_cal:
                disp_cal[key] = []
            disp_cal[key].append({
                'inicio': d.hora_inicio.strftime('%H:%M'),
                'fin'   : d.hora_fin.strftime('%H:%M'),
            })
        disponibilidades_json = json.dumps(disp_cal)

        # Historial del doctor: citas cerradas en su consultorio
        from django.core.paginator import Paginator as Pag
        qs_historial = (
            Reserva.objects
            .filter(
                profesional=profesional,
                estado__in=['completada', 'seguimiento', 'no_asistio', 'cancelada'],
            )
            .select_related('paciente__usuario')
            .order_by('-fecha_reserva')
        )
        total_historial = qs_historial.count()
        pag_historial   = Pag(qs_historial, 15)
        page_historial  = pag_historial.get_page(request.GET.get('page_h'))

    horas_disponibles = [
        f"{h:02d}:{m:02d}"
        for h in range(7, 21)
        for m in (0, 30)
    ]

    consultorios = Consultorio.objects.all().order_by('nom_reg', 'nombre')

    return render(request, 'panel_doctor.html', {
        'title'               : 'Panel del Doctor',
        'profesional'         : profesional,
        'consultorios'        : consultorios,
        'reservas_hoy'        : reservas_hoy,
        'reservas_pendientes' : reservas_pendientes,
        'disponibilidades'    : disponibilidades,
        'total_hoy'           : total_hoy,
        'total_pendientes'    : total_pendientes,
        'total_completadas'   : total_completadas,
        'fecha_hoy'           : hoy,
        'horas_disponibles'   : horas_disponibles,
        'tab_activa'            : tab_activa,
        'error_disponibilidad'  : error_disponibilidad,
        'reservas_sin_gestionar': reservas_sin_gestionar,
        'total_sin_gestionar'   : total_sin_gestionar,
        'page_historial'        : page_historial,
        'total_historial'       : total_historial,
        'disponibilidades_json' : disponibilidades_json,
    })