from flask import Blueprint, request, render_template, redirect, url_for, session
from models.usuario import Usuario
from app import db
import datetime
import random
import string

auth_routes = Blueprint('auth_routes', __name__)

@auth_routes.route('/login', methods=['GET'])
def login_form():
    return render_template('login.html')

@auth_routes.route('/register', methods=['GET'])
def register_form():
    return render_template('register.html')

@auth_routes.route('/login', methods=['POST'])
def login():
    correo = request.form.get('correo')
    contrasena = request.form.get('contrasena')

    usuario = Usuario.query.filter_by(correo=correo).first()
    if not usuario or not usuario.check_password(contrasena):
        return render_template('login.html', error='Credenciales inválidas')

    session['user_id'] = usuario.id
    session['nombre_completo'] = usuario.nombre_completo

    if usuario.debe_cambiar_contrasena:
        return redirect(url_for('auth_routes.cambiar_contrasena'))

    # Redirecciones por rol
    if usuario.rol == 'administrador':
        return redirect(url_for('admin_routes.dashboard'))

    elif usuario.rol == 'empleado':
        # 🔥 Importante: redirigimos al panel de empleados,
        # que ya carga mesas, productos y órdenes correctamente.
        return redirect(url_for('empleados_routes.empleado_panel'))

    elif usuario.rol == 'cliente':
        return redirect(url_for('cliente_routes.index'))

    return render_template('login.html', error='Rol no reconocido')

@auth_routes.route('/register', methods=['POST'])
def register():
    nombre = request.form.get('nombre_completo') or request.json.get('nombre_completo')
    correo = request.form.get('correo') or request.json.get('correo')
    contrasena = request.form.get('contrasena') or request.json.get('contrasena')
    telefono = request.form.get('telefono') or request.json.get('telefono')

    if not nombre or not correo or not contrasena:
        return render_template('register.html', error='Faltan campos requeridos')

    if Usuario.query.filter_by(correo=correo).first():
        return render_template('register.html', error='El correo ya está registrado')

    nuevo_usuario = Usuario(
        nombre_completo=nombre,
        correo=correo,
        telefono=telefono,
        rol='cliente',
        fecha_creacion=datetime.datetime.utcnow()
    )

    nuevo_usuario.set_password(contrasena)
    db.session.add(nuevo_usuario)
    db.session.commit()

    return render_template('register.html', mensaje='Usuario registrado correctamente')

@auth_routes.route('/logout')
def logout():
    session.clear()
    return render_template('paginaprin.html')

@auth_routes.route('/cambiar_contrasena', methods=['GET', 'POST'])
def cambiar_contrasena():
    if 'user_id' not in session:
        return redirect(url_for('auth_routes.login_form'))

    usuario = Usuario.query.get(session['user_id'])
    if request.method == 'POST':
        nueva = request.form['nueva_contrasena']
        usuario.set_password(nueva)
        usuario.debe_cambiar_contrasena = False
        db.session.commit()

        # Redirigir según el rol
        if usuario.rol == 'administrador':
            return redirect(url_for('admin_routes.dashboard'))

        elif usuario.rol == 'empleado':
            return redirect(url_for('empleados_routes.empleado_panel'))

        elif usuario.rol == 'cliente':
            return redirect(url_for('cliente_routes.index'))  # Corregido

        else:
            return render_template('login.html', error='Rol no reconocido')

    return render_template('cambiar_contrasena.html', usuario=usuario)

@auth_routes.route('/recuperar_contrasena', methods=['GET', 'POST'])
def recuperar_contrasena():
    mensaje = None
    if request.method == 'POST':
        correo = request.form.get('correo')
        usuario = Usuario.query.filter_by(correo=correo).first()
        if usuario:
            temp_pass = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            usuario.set_password(temp_pass)
            usuario.debe_cambiar_contrasena = True
            db.session.commit()
            from routes.admin_routes import enviar_correo
            enviar_correo(correo, temp_pass, nombre_completo=usuario.nombre_completo)
            mensaje = 'Se ha enviado una nueva contraseña temporal a tu correo.'
        else:
            mensaje = 'El correo no está registrado.'
    return render_template('recuperar_contrasena.html', mensaje=mensaje)