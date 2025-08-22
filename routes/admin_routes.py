from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from models.usuario import Usuario
from models.categoria import Categoria
from models.producto import Producto
from app import db
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from werkzeug.utils import secure_filename
from flask import session

admin_routes = Blueprint('admin_routes', __name__)

def enviar_correo(destinatario, contrasena_temporal, nombre_completo=None):
    remitente = 'cafeterialasdosamigas@gmail.com'
    password = 'doehmsrgujcalrrj'

    mensaje = MIMEMultipart()
    mensaje['From'] = remitente
    mensaje['To'] = destinatario
    mensaje['Subject'] = 'Tu nueva contraseña temporal'

    saludo = f"¡Bienvenido {nombre_completo}!" if nombre_completo else "¡Bienvenido!"

    cuerpo = f"""
{saludo}

Tu nueva contraseña temporal es: {contrasena_temporal}

Por favor cámbiala después de iniciar sesión.
"""
    mensaje.attach(MIMEText(cuerpo, 'plain', 'utf-8'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(remitente, password)
            server.sendmail(remitente, destinatario, mensaje.as_string())
        print("Correo enviado correctamente.")
    except Exception as e:
        print(f"Error al enviar correo: {e}")


# ---------------------------
# DASHBOARD
# ---------------------------
@admin_routes.route('/dashboard', methods=['GET'])
def dashboard():
    usuarios = Usuario.query.all()
    categorias = Categoria.query.all()
    productos = Producto.query.all()

    # últimos registros
    ultimos_empleados = Usuario.query.filter_by(rol='empleado').order_by(Usuario.id.desc()).limit(5).all()
    ultimos_productos = Producto.query.order_by(Producto.id.desc()).limit(5).all()
    nombre_admin = session.get('nombre_completo')

    return render_template(
        'admin/dashboard.html',
        usuarios=usuarios,
        categorias=categorias,
        productos=productos,
        ultimos_empleados=ultimos_empleados,
        ultimos_productos=ultimos_productos,
        nombre_admin=nombre_admin 
    )


# ---------------------------
# PRODUCTOS
# ---------------------------
@admin_routes.route('/anadir_producto', methods=['POST'])
def anadir_producto():
    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    precio = float(request.form.get('precio'))
    es_rotativo = bool(int(request.form.get('es_rotativo')))
    categorias_id_raw = request.form.get('categorias_id')

    imagen = request.files.get('imagen')
    imagen_url = None
    if imagen and imagen.filename != '':
        filename = secure_filename(imagen.filename)
        carpeta_destino = os.path.join('static', 'img')
        os.makedirs(carpeta_destino, exist_ok=True)
        ruta = os.path.join(carpeta_destino, filename)
        imagen.save(ruta)
        imagen_url = f'/static/img/{filename}'

    if not categorias_id_raw:
        flash('Debes seleccionar una categoría.', 'error')
    else:
        try:
            categorias_id = int(categorias_id_raw)
            nuevo_producto = Producto(
                nombre=nombre,
                descripcion=descripcion,
                precio=precio,
                es_rotativo=es_rotativo,
                categorias_id=categorias_id,
                imagen_url=imagen_url
            )
            db.session.add(nuevo_producto)
            db.session.commit()
            flash('Producto agregado correctamente.', 'success')
        except Exception as e:
            flash(f'Error al agregar producto: {str(e)}', 'error')

    return redirect(url_for('admin_routes.dashboard'))


@admin_routes.route('/editar_producto/<int:id>', methods=['POST'])
def editar_producto(id):
    producto = Producto.query.get_or_404(id)

    producto.nombre = request.form.get('nombre')
    producto.descripcion = request.form.get('descripcion')
    producto.precio = float(request.form.get('precio'))

    imagen = request.files.get('imagen')
    if imagen and imagen.filename != '':
        filename = secure_filename(imagen.filename)
        carpeta_destino = os.path.join('static', 'img')
        os.makedirs(carpeta_destino, exist_ok=True)
        ruta = os.path.join(carpeta_destino, filename)
        imagen.save(ruta)
        producto.imagen_url = f'/static/img/{filename}'

    try:
        db.session.commit()
        flash('Producto actualizado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar producto: {str(e)}', 'error')

    return redirect(url_for('admin_routes.dashboard'))


@admin_routes.route('/eliminar_producto/<int:id>', methods=['POST'])
def eliminar_producto(id):
    producto = Producto.query.get_or_404(id)
    try:
        db.session.delete(producto)
        db.session.commit()
        flash('Producto eliminado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar producto: {str(e)}', 'error')
    return redirect(url_for('admin_routes.dashboard'))


# ---------------------------
# EMPLEADOS
# ---------------------------
@admin_routes.route('/add_empleado', methods=['POST'])
def add_empleado():
    nombre = request.form.get('nombre_completo')
    correo = request.form.get('correo')
    contrasena_temporal = 'abc123Ñ'

    nuevo_empleado = Usuario(
        nombre_completo=nombre,
        correo=correo,
        rol='empleado',
        debe_cambiar_contrasena=True
    )
    nuevo_empleado.set_password(contrasena_temporal)

    db.session.add(nuevo_empleado)
    db.session.commit()

    enviar_correo(correo, contrasena_temporal, nombre_completo=nombre)
    flash('Empleado agregado y correo enviado.', 'success')

    return redirect(url_for('admin_routes.dashboard'))


@admin_routes.route('/editar_empleado/<int:id>', methods=['POST'])
def editar_empleado(id):
    empleado = Usuario.query.get_or_404(id)

    empleado.nombre_completo = request.form.get('nombre_completo')
    empleado.correo = request.form.get('correo')

    try:
        db.session.commit()
        flash('Empleado actualizado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar empleado: {str(e)}', 'error')

    return redirect(url_for('admin_routes.dashboard'))


@admin_routes.route('/eliminar_empleado/<int:id>', methods=['POST'])
def eliminar_empleado(id):
    empleado = Usuario.query.get_or_404(id)
    try:
        db.session.delete(empleado)
        db.session.commit()
        flash('Empleado eliminado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar empleado: {str(e)}', 'error')

    return redirect(url_for('admin_routes.dashboard'))