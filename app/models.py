# app/models.py
from flask_login import UserMixin
from . import db
from datetime import date

# --- Empleado ---
class Empleado(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    contrasena = db.Column(db.String(128), nullable=False)
    rol = db.Column(db.String(20), default='empleado')  # 'administrador' o 'empleado'
    fecha_registro = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relaciones
    jornadas = db.relationship('Jornada', backref='empleado', lazy=True)
    ausencias = db.relationship('Ausencia', backref='empleado', lazy=True)

# --- Jornada ---
class Jornada(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleado.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    horas_trabajadas = db.Column(db.Float, nullable=False)
    comentario = db.Column(db.String(200))
    estado = db.Column(db.String(20), default='pendiente')  # Nuevo campo


# --- Ausencia ---
class Ausencia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleado.id'), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    motivo = db.Column(db.String(200))
    estado = db.Column(db.String(20), default='pendiente')  # Nuevo campo
    tipo = db.Column(db.String(50), nullable=False, default='otro')
