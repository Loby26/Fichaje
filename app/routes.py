# app/routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import Empleado, Jornada, Ausencia
from . import db
from datetime import date, timedelta
from werkzeug.security import generate_password_hash

# Crear blueprint
main = Blueprint('main', __name__)

# ===========================
# Página de inicio
# ===========================
@main.route('/')
@login_required
def index():
    # Datos resumen
    total_empleados = Empleado.query.count()
    jornadas_hoy = Jornada.query.filter_by(fecha=date.today()).count()
    total_jornadas = Jornada.query.count()
    ausencias_activas = Ausencia.query.filter(
        Ausencia.fecha_inicio <= date.today(),
        Ausencia.fecha_fin >= date.today()
    ).count()

    # Últimos empleados
    ultimos_empleados = Empleado.query.order_by(Empleado.id.desc()).limit(5).all()

    # Últimas jornadas
    ultimas_jornadas = Jornada.query.order_by(Jornada.fecha.desc()).limit(5).all()

    return render_template(
        'index.html',
        total_empleados=total_empleados,
        jornadas_hoy=jornadas_hoy,
        total_jornadas=total_jornadas,
        ausencias_activas=ausencias_activas,
        ultimos_empleados=ultimos_empleados,
        ultimas_jornadas=ultimas_jornadas
    )

# ===========================
# Gestión de empleados (solo ADMIN)
# ===========================
@main.route('/empleados', methods=['GET', 'POST'])
@login_required
def empleados():
    if current_user.rol != 'administrador':
        flash('No tienes permisos para acceder a la gestión de empleados.', 'error')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        contrasena = request.form['contrasena']
        rol = request.form.get('rol', 'empleado')

        if Empleado.query.filter_by(email=email).first():
            flash('El email ya está registrado.', 'error')
            return redirect(url_for('main.empleados'))

        contrasena_hash = generate_password_hash(contrasena)

        nuevo_empleado = Empleado(
            nombre=nombre,
            email=email,
            contrasena=contrasena_hash,
            rol=rol
        )
        db.session.add(nuevo_empleado)
        db.session.commit()

        flash('Empleado creado correctamente.', 'success')
        return redirect(url_for('main.empleados'))

    empleados = Empleado.query.order_by(Empleado.fecha_registro.desc()).all()
    return render_template('empleados/empleados.html', empleados=empleados)


# ===========================
# Gestión de jornadas
# ===========================
@main.route('/jornadas', methods=['GET', 'POST'])
@login_required
def jornadas():
    if request.method == 'POST':
        # Si es admin puede elegir empleado
        if current_user.rol == 'administrador':
            empleado_id = int(request.form['empleado_id'])
        else:
            empleado_id = current_user.id  # el usuario actual

        fecha = request.form['fecha']
        horas_trabajadas = float(request.form['horas_trabajadas'])
        comentario = request.form.get('comentario', '')

        nueva_jornada = Jornada(
            empleado_id=empleado_id,
            fecha=date.fromisoformat(fecha),
            horas_trabajadas=horas_trabajadas,
            comentario=comentario,
            estado='pendiente'  # no olvides este campo si lo tienes en el modelo
        )
        db.session.add(nueva_jornada)
        db.session.commit()

        flash('Jornada registrada correctamente. Ahora está pendiente de aprobación.', 'success')
        return redirect(url_for('main.jornadas'))

    # Listado:
    if current_user.rol == 'administrador':
        jornadas = Jornada.query.order_by(Jornada.fecha.desc()).all()
        empleados = Empleado.query.order_by(Empleado.nombre).all()  # Para el selector del formulario
    else:
        jornadas = Jornada.query.filter_by(empleado_id=current_user.id).order_by(Jornada.fecha.desc()).all()
        empleados = None  # no se necesita

    return render_template('jornadas/jornadas.html', jornadas=jornadas, empleados=empleados)

@main.route('/panel-validaciones', methods=['GET', 'POST'])
@login_required
def panel_validaciones():
    if current_user.rol != 'administrador':
        flash('No tienes permisos para acceder al panel de validaciones.', 'danger')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        tipo = request.form.get('tipo')
        accion = request.form.get('accion')

        if tipo == 'jornada':
            jornada_id = request.form.get('jornada_id')
            jornada = Jornada.query.get(jornada_id)
            if jornada:
                if accion == 'aceptar':
                    jornada.estado = 'aceptada'
                elif accion == 'rechazar':
                    jornada.estado = 'rechazada'
                db.session.commit()
                flash(f'Jornada {jornada.id} actualizada a {jornada.estado}.', 'success')
            else:
                flash('Jornada no encontrada.', 'danger')

        elif tipo == 'ausencia':
            ausencia_id = request.form.get('ausencia_id')
            ausencia = Ausencia.query.get(ausencia_id)
            if ausencia:
                if accion == 'aceptar':
                    ausencia.estado = 'aceptada'
                elif accion == 'rechazar':
                    ausencia.estado = 'rechazada'
                db.session.commit()
                flash(f'Ausencia {ausencia.id} actualizada a {ausencia.estado}.', 'success')
            else:
                flash('Ausencia no encontrada.', 'danger')

        return redirect(url_for('main.panel_validaciones'))

    # GET → traer pendientes
    jornadas_pendientes = Jornada.query.filter_by(estado='pendiente').order_by(Jornada.fecha.desc()).all()
    ausencias_pendientes = Ausencia.query.filter_by(estado='pendiente').order_by(Ausencia.fecha_inicio.desc()).all()

    return render_template(
        'jornadas/panel_admin.html',
        jornadas=jornadas_pendientes,
        ausencias=ausencias_pendientes
    )


# ===========================
# Gestión de ausencias
# ===========================
@main.route('/ausencias', methods=['GET', 'POST'])
@login_required
def ausencias():
    if request.method == 'POST':
        empleado_id = request.form['empleado_id']
        fecha_inicio = request.form['fecha_inicio']
        fecha_fin = request.form['fecha_fin']
        motivo = request.form.get('motivo', '')
        tipo = request.form.get('tipo', 'otro')  # NUEVO CAMPO

        nueva_ausencia = Ausencia(
            empleado_id=empleado_id,
            fecha_inicio=date.fromisoformat(fecha_inicio),
            fecha_fin=date.fromisoformat(fecha_fin),
            motivo=motivo,
            tipo=tipo,
            estado='pendiente'  # si ya tienes validación
        )
        db.session.add(nueva_ausencia)
        db.session.commit()

        flash('Ausencia registrada correctamente. Ahora está pendiente de aprobación.', 'success')
        return redirect(url_for('main.ausencias'))

    if current_user.rol == 'administrador':
        ausencias = Ausencia.query.all()
        empleados = Empleado.query.all()
    else:
        # Si es empleado, solo ve sus ausencias
        ausencias = Ausencia.query.filter_by(empleado_id=current_user.id).all()
        empleados = [current_user]

    return render_template('ausencias/ausencias.html', ausencias=ausencias, empleados=empleados)

@main.route('/calendario-ausencias')
@login_required
def calendario_ausencias():
    from calendar import monthrange
    from datetime import date

    # Leer parámetros de URL, si no se pasan → mes actual
    year = request.args.get('year', default=date.today().year, type=int)
    month = request.args.get('month', default=date.today().month, type=int)

    # Evitar valores inválidos
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1

    # Obtener el número de días del mes
    _, num_days = monthrange(year, month)

    # Ausencias en ese mes
    ausencias = Ausencia.query.filter(
        Ausencia.fecha_inicio <= date(year, month, num_days),
        Ausencia.fecha_fin >= date(year, month, 1)
    ).all()

    # Mapeo día → ausencias
    calendario = {day: [] for day in range(1, num_days + 1)}

    for ausencia in ausencias:
        inicio = max(ausencia.fecha_inicio.day, 1) if ausencia.fecha_inicio.month == month else 1
        fin = min(ausencia.fecha_fin.day, num_days) if ausencia.fecha_fin.month == month else num_days

        for day in range(inicio, fin + 1):
            calendario[day].append({
                'nombre': ausencia.empleado.nombre,
                'motivo': ausencia.motivo
            })

    return render_template(
        'ausencias/calendario.html',
        calendario=calendario,
        year=year,
        month=month
    )
