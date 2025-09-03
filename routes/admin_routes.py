from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from models.usuario import Usuario
from models.categoria import Categoria
from models.producto import Producto
from models.venta import Venta
from models.detalle_venta import DetalleVenta
from app import db
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from werkzeug.utils import secure_filename
from datetime import date, datetime, timedelta

admin_routes = Blueprint('admin_routes', __name__)

# ---------------------------
# EMAIL
# ---------------------------
def enviar_correo(destinatario, contrasena_temporal, nombre_completo=None):
    remitente = 'cafeterialasdosamigas@gmail.com'
    password = 'doehmsrgujcalrrlr'  # Actualiza con la contraseña real

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

    # Empleados (solo rol empleado)
    empleados = Usuario.query.filter_by(rol='empleado').all()

    # Clientes (rol cliente)
    clientes = Usuario.query.filter_by(rol='cliente').all()

    # Últimos registros
    ultimos_empleados = Usuario.query.filter_by(rol='empleado').order_by(Usuario.id.desc()).limit(5).all()
    ultimos_productos = Producto.query.order_by(Producto.id.desc()).limit(5).all()
    ultimos_clientes = Usuario.query.filter_by(rol='cliente').order_by(Usuario.id.desc()).limit(5).all()
    nombre_admin = session.get('nombre_completo')

    # Estadísticas generales
    total_empleados = len(empleados)
    total_clientes = len(clientes)
    hoy = date.today()
    ventas_hoy = (
        db.session.query(db.func.sum(Venta.total))
        .filter(db.func.date(Venta.fecha) == hoy)
        .scalar()
    ) or 0
    pedidos = (
        db.session.query(Venta)
        .filter(db.func.date(Venta.fecha) == hoy)
        .count()
    )

    # Historial de ventas por método de pago (del día actual)
    ventas_efectivo = (
        db.session.query(db.func.sum(Venta.total))
        .filter(db.func.date(Venta.fecha) == hoy, Venta.metodo_pago == 'Efectivo')
        .scalar()
    ) or 0
    ventas_tarjeta = (
        db.session.query(db.func.sum(Venta.total))
        .filter(db.func.date(Venta.fecha) == hoy, Venta.metodo_pago == 'Tarjeta')
        .scalar()
    ) or 0
    ventas_transferencia = (
        db.session.query(db.func.sum(Venta.total))
        .filter(db.func.date(Venta.fecha) == hoy, Venta.metodo_pago == 'Transferencia')
        .scalar()
    ) or 0

    # Productos con bajo stock (cantidad <= 10)
    productos_bajo_stock = [p for p in productos if p.cantidad <= 10]

    return render_template(
        'admin/dashboard.html',
        usuarios=usuarios,
        empleados=empleados,
        clientes=clientes,  # Agregado
        categorias=categorias,
        productos=productos,
        ultimos_empleados=ultimos_empleados,
        ultimos_productos=ultimos_productos,
        ultimos_clientes=ultimos_clientes,  # Agregado
        nombre_admin=nombre_admin,
        total_empleados=total_empleados,
        total_clientes=total_clientes,  # Agregado
        ventas_hoy=ventas_hoy,
        pedidos=pedidos,
        ventas_efectivo=ventas_efectivo,  # Agregado
        ventas_tarjeta=ventas_tarjeta,  # Agregado
        ventas_transferencia=ventas_transferencia,  # Agregado
        productos_bajo_stock=productos_bajo_stock  # Agregado
    )

# ---------------------------
# PRODUCTOS
# ---------------------------
@admin_routes.route('/anadir_producto', methods=['POST'])
def anadir_producto():
    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    precio = float(request.form.get('precio'))
    es_rotativo = bool(int(request.form.get('es_rotativo', 0)))
    cantidad = int(request.form.get('cantidad', 0))   # 👈 cantidad siempre int
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
                imagen_url=imagen_url,
                cantidad=cantidad  # 👈 agregado
            )
            db.session.add(nuevo_producto)
            db.session.commit()
            flash('Producto agregado correctamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al agregar producto: {str(e)}', 'error')

    return redirect(url_for('admin_routes.dashboard'))

@admin_routes.route('/editar_producto/<int:id>', methods=['POST'])
def editar_producto(id):
    producto = Producto.query.get_or_404(id)

    producto.nombre = request.form.get('nombre')
    producto.descripcion = request.form.get('descripcion')
    producto.precio = float(request.form.get('precio'))
    producto.cantidad = int(request.form.get('cantidad', producto.cantidad or 0))  # 👈 se puede editar

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

# ---------------------------
# CLIENTES
# ---------------------------
@admin_routes.route('/add_cliente', methods=['POST'])
def add_cliente():
    nombre = request.form.get('nombre_completo')
    correo = request.form.get('correo')
    contrasena_temporal = 'abc123Ñ'

    nuevo_cliente = Usuario(
        nombre_completo=nombre,
        correo=correo,
        rol='cliente',
        debe_cambiar_contrasena=True
    )
    nuevo_cliente.set_password(contrasena_temporal)

    db.session.add(nuevo_cliente)
    db.session.commit()

    enviar_correo(correo, contrasena_temporal, nombre_completo=nombre)
    flash('Cliente agregado y correo enviado.', 'success')

    return redirect(url_for('admin_routes.dashboard'))

@admin_routes.route('/editar_cliente/<int:id>', methods=['POST'])
def editar_cliente(id):
    cliente = Usuario.query.get_or_404(id)

    cliente.nombre_completo = request.form.get('nombre_completo')
    cliente.correo = request.form.get('correo')

    try:
        db.session.commit()
        flash('Cliente actualizado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar cliente: {str(e)}', 'error')

    return redirect(url_for('admin_routes.dashboard'))

@admin_routes.route('/eliminar_cliente/<int:id>', methods=['POST'])
def eliminar_cliente(id):
    cliente = Usuario.query.get_or_404(id)
    try:
        db.session.delete(cliente)
        db.session.commit()
        flash('Cliente eliminado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar cliente: {str(e)}', 'error')

    return redirect(url_for('admin_routes.dashboard'))