# app/auth.py

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from .models import Empleado
from . import db

auth = Blueprint('auth', __name__)

# =============== LOGIN ===============
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form['email']
        contrasena = request.form['contrasena']

        empleado = Empleado.query.filter_by(email=email).first()

        if empleado and check_password_hash(empleado.contrasena, contrasena):
            login_user(empleado)
            flash('Has iniciado sesión correctamente.', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Credenciales incorrectas.', 'danger')

    return render_template('auth/login.html')

# =============== LOGOUT ===============
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión.', 'success')
    return redirect(url_for('auth.login'))

# =============== REGISTRO (PRIMER USUARIO ADMIN) ===============
@auth.route('/register', methods=['GET', 'POST'])
def register():
    # Solo permitir si no hay ningún usuario creado aún
    if Empleado.query.count() > 0 and not current_user.is_authenticated:
        flash('El registro está cerrado. Contacta con un administrador.', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        contrasena = request.form['contrasena']

        # Hash de contraseña
        hashed_password = generate_password_hash(contrasena)

        # Si es el primer usuario → administrador
        rol = 'administrador' if Empleado.query.count() == 0 else 'empleado'

        nuevo = Empleado(
            nombre=nombre,
            email=email,
            contrasena=hashed_password,
            rol=rol
        )
        db.session.add(nuevo)
        db.session.commit()

        flash('Usuario registrado correctamente. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')
