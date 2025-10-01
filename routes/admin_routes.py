from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from models.usuario import Usuario
from models.categoria import Categoria
from models.producto import Producto
from models.venta import Venta
from models.detalle_venta import DetalleVenta
from models.orden import Orden
from app import db
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from werkzeug.utils import secure_filename
from datetime import date, datetime, timedelta
from config import settings
from models.notificacion import Notificacion
import json

admin_routes = Blueprint('admin_routes', __name__)

# ---------------------------
# EMAIL
# ---------------------------
def enviar_correo(destinatario, contrasena_temporal, nombre_completo=None):
    remitente = settings.EMAIL_USER or 'cafeterialasdosamigas@gmail.com'
    password = settings.EMAIL_PASS or 'doehmsrgujcalrrlr'

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
        return True
    except Exception as e:
        print(f"Error al enviar correo: {e}")
        flash(f'Error al enviar correo: {str(e)}', 'error')
        return False

# ---------------------------
# DASHBOARD
# ---------------------------
@admin_routes.route('/dashboard', methods=['GET'])
def dashboard():
    usuarios = Usuario.query.all()
    categorias = Categoria.query.all()
    productos = Producto.query.all()
    empleados = Usuario.query.filter_by(rol='empleado').all()
    clientes = Usuario.query.filter_by(rol='cliente').all()

    ultimos_empleados = Usuario.query.filter_by(rol='empleado').order_by(Usuario.id.desc()).limit(5).all()
    ultimos_productos = Producto.query.order_by(Producto.id.desc()).limit(5).all()
    ultimos_clientes = Usuario.query.filter_by(rol='cliente').order_by(Usuario.id.desc()).limit(5).all()
    nombre_admin = session.get('nombre_completo')

    total_empleados = len(empleados)
    total_clientes = len(clientes)
    hoy = date.today()

    # Ventas totales hoy (suma de Venta + Orden pagadas)
    ventas_hoy_ventas = (db.session.query(db.func.sum(Venta.total)).filter(db.func.date(Venta.fecha) == hoy).scalar()) or 0
    ventas_hoy_ordenes = (db.session.query(db.func.sum(Orden.total)).filter(db.func.date(Orden.fecha_creacion) == hoy, Orden.estado == 'pagado').scalar()) or 0
    ventas_hoy = ventas_hoy_ventas + ventas_hoy_ordenes

    # Pedidos totales hoy (conteo de Venta + Orden pagadas)
    pedidos_ventas = db.session.query(Venta).filter(db.func.date(Venta.fecha) == hoy).count()
    pedidos_ordenes = db.session.query(Orden).filter(db.func.date(Orden.fecha_creacion) == hoy, Orden.estado == 'pagado').count()
    pedidos = pedidos_ventas + pedidos_ordenes

    # Desglose por método de pago (suma de ambos modelos)
    # Efectivo
    efectivo_ventas = (db.session.query(db.func.sum(Venta.total)).filter(db.func.date(Venta.fecha) == hoy, Venta.metodo_pago == 'Efectivo').scalar()) or 0
    efectivo_ordenes = (db.session.query(db.func.sum(Orden.total)).filter(db.func.date(Orden.fecha_creacion) == hoy, Orden.estado == 'pagado', Orden.metodo_pago == 'Efectivo').scalar()) or 0
    ventas_efectivo = efectivo_ventas + efectivo_ordenes

    # Tarjeta
    tarjeta_ventas = (db.session.query(db.func.sum(Venta.total)).filter(db.func.date(Venta.fecha) == hoy, Venta.metodo_pago == 'Tarjeta').scalar()) or 0
    tarjeta_ordenes = (db.session.query(db.func.sum(Orden.total)).filter(db.func.date(Orden.fecha_creacion) == hoy, Orden.estado == 'pagado', Orden.metodo_pago == 'Tarjeta').scalar()) or 0
    ventas_tarjeta = tarjeta_ventas + tarjeta_ordenes

    # Transferencia
    transferencia_ventas = (db.session.query(db.func.sum(Venta.total)).filter(db.func.date(Venta.fecha) == hoy, Venta.metodo_pago == 'Transferencia').scalar()) or 0
    transferencia_ordenes = (db.session.query(db.func.sum(Orden.total)).filter(db.func.date(Orden.fecha_creacion) == hoy, Orden.estado == 'pagado', Orden.metodo_pago == 'Transferencia').scalar()) or 0
    ventas_transferencia = transferencia_ventas + transferencia_ordenes

    # Historial de ventas por día
    # Obtener fechas distintas de Venta y Orden
    fechas_ventas = db.session.query(db.func.date(Venta.fecha).label('fecha')).distinct().all()
    fechas_ordenes = db.session.query(db.func.date(Orden.fecha_creacion).label('fecha')).filter(Orden.estado == 'pagado').distinct().all()
    fechas = set([f.fecha for f in fechas_ventas] + [f.fecha for f in fechas_ordenes])
    sales_history = []

    for fecha in sorted(fechas, reverse=True):
        # Suma de totales por día
        total_ventas = (db.session.query(db.func.sum(Venta.total)).filter(db.func.date(Venta.fecha) == fecha).scalar()) or 0
        total_ordenes = (db.session.query(db.func.sum(Orden.total)).filter(db.func.date(Orden.fecha_creacion) == fecha, Orden.estado == 'pagado').scalar()) or 0
        total = total_ventas + total_ordenes

        # Desglose por método de pago
        efectivo_ventas = (db.session.query(db.func.sum(Venta.total)).filter(db.func.date(Venta.fecha) == fecha, Venta.metodo_pago == 'Efectivo').scalar()) or 0
        efectivo_ordenes = (db.session.query(db.func.sum(Orden.total)).filter(db.func.date(Orden.fecha_creacion) == fecha, Orden.estado == 'pagado', Orden.metodo_pago == 'Efectivo').scalar()) or 0
        efectivo = efectivo_ventas + efectivo_ordenes

        tarjeta_ventas = (db.session.query(db.func.sum(Venta.total)).filter(db.func.date(Venta.fecha) == fecha, Venta.metodo_pago == 'Tarjeta').scalar()) or 0
        tarjeta_ordenes = (db.session.query(db.func.sum(Orden.total)).filter(db.func.date(Orden.fecha_creacion) == fecha, Orden.estado == 'pagado', Orden.metodo_pago == 'Tarjeta').scalar()) or 0
        tarjeta = tarjeta_ventas + tarjeta_ordenes

        transferencia_ventas = (db.session.query(db.func.sum(Venta.total)).filter(db.func.date(Venta.fecha) == fecha, Venta.metodo_pago == 'Transferencia').scalar()) or 0
        transferencia_ordenes = (db.session.query(db.func.sum(Orden.total)).filter(db.func.date(Orden.fecha_creacion) == fecha, Orden.estado == 'pagado', Orden.metodo_pago == 'Transferencia').scalar()) or 0
        transferencia = transferencia_ventas + transferencia_ordenes

        sales_history.append({
            'date': fecha.strftime('%Y-%m-%d'),
            'total': total,
            'efectivo': efectivo,
            'tarjeta': tarjeta,
            'transferencia': transferencia
        })

    productos_bajo_stock = [p for p in productos if p.cantidad <= 10]
    notificaciones = Notificacion.query.order_by(Notificacion.fecha.desc()).limit(10).all()
    # Procesar datos JSON
    for n in notificaciones:
        try:
            n.datos_dict = json.loads(n.datos) if n.datos else {}
        except Exception:
            n.datos_dict = {}
    return render_template(
        'admin/dashboard.html',
        usuarios=usuarios,
        empleados=empleados, 
        clientes=clientes,
        categorias=categorias,
        productos=productos,
        ultimos_empleados=ultimos_empleados,
        ultimos_productos=ultimos_productos,
        ultimos_clientes=ultimos_clientes,
        nombre_admin=nombre_admin,
        total_empleados=total_empleados,
        total_clientes=total_clientes,
        ventas_hoy=ventas_hoy,
        pedidos=pedidos,
        ventas_efectivo=ventas_efectivo,
        ventas_tarjeta=ventas_tarjeta,
        ventas_transferencia=ventas_transferencia,
        productos_bajo_stock=productos_bajo_stock,
        sales_history=sales_history,
        notificaciones=notificaciones,
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
    cantidad = int(request.form.get('cantidad', 0))
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
                cantidad=cantidad
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
    try:
        producto.precio = float(request.form.get('precio'))
    except ValueError:
        flash('El precio debe ser un número válido.', 'error')
        return redirect(url_for('admin_routes.dashboard'))

    try:
        producto.categorias_id = int(request.form.get('categorias_id'))
    except (ValueError, TypeError):
        flash('Debes seleccionar una categoría válida.', 'error')
        return redirect(url_for('admin_routes.dashboard'))

    producto.es_rotativo = 'es_rotativo' in request.form
    try:
        producto.cantidad = int(request.form.get('cantidad', 0))
    except ValueError:
        flash('La cantidad debe ser un número válido.', 'error')
        return redirect(url_for('admin_routes.dashboard'))

    # Imagen opcional
    imagen = request.files.get('imagen')
    if imagen and imagen.filename != "":
        try:
            filename = secure_filename(imagen.filename)
            carpeta_destino = os.path.join('static', 'img')
            os.makedirs(carpeta_destino, exist_ok=True)
            ruta = os.path.join(carpeta_destino, filename)
            imagen.save(ruta)
            producto.imagen_url = f'/static/img/{filename}'  # ✅ mantiene la nueva
        except Exception as e:
            flash(f'Error al guardar la imagen: {str(e)}', 'error')
            return redirect(url_for('admin_routes.dashboard'))
    # 👇 Si no hay imagen nueva, conserva la anterior (no tocamos producto.imagen_url)

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
        # Eliminar todos los detalles de venta asociados al producto
        detalle_count = DetalleVenta.query.filter_by(producto_id=producto.id).delete(synchronize_session='fetch')
        if detalle_count > 0:
            print(f"Eliminados {detalle_count} detalles de venta para el producto {producto.id}")
        
        # Eliminar el producto
        db.session.delete(producto)
        db.session.commit()
        flash('Producto y sus detalles asociados eliminados correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar producto: {str(e)}', 'error')
        print(f"Error detallado: {str(e)}")  # Depuración

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

    if enviar_correo(correo, contrasena_temporal, nombre_completo=nombre):
        flash('Empleado agregado y correo enviado.', 'success')
    else:
        flash('Empleado agregado, pero falló el envío de correo.', 'warning')

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
    telefono = request.form.get('telefono')
    direccion = request.form.get('direccion')
    contrasena_temporal = 'abc123Ñ'

    nuevo_cliente = Usuario(
        nombre_completo=nombre,
        correo=correo,
        telefono=telefono,
        direccion=direccion,
        rol='cliente',
        debe_cambiar_contrasena=True
    )
    nuevo_cliente.set_password(contrasena_temporal)

    db.session.add(nuevo_cliente)
    db.session.commit()

    if enviar_correo(correo, contrasena_temporal, nombre_completo=nombre):
        flash('Cliente agregado y correo enviado.', 'success')
    else:
        flash('Cliente agregado, pero falló el envío de correo.', 'warning')

    return redirect(url_for('admin_routes.dashboard'))

@admin_routes.route('/editar_cliente/<int:id>', methods=['POST'])
def editar_cliente(id):
    cliente = Usuario.query.get_or_404(id)

    cliente.nombre_completo = request.form.get('nombre_completo')
    cliente.correo = request.form.get('correo')
    cliente.telefono = request.form.get('telefono')
    cliente.direccion = request.form.get('direccion')

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
        # Obtener todas las ventas asociadas al cliente
        ventas = Venta.query.filter_by(usuarios_id=cliente.id).all()
        if ventas:
            for venta in ventas:
                # Eliminar detalles de venta asociados
                DetalleVenta.query.filter_by(venta_id=venta.id).delete(synchronize_session='fetch')
                # Eliminar la venta
                db.session.delete(venta)
        
        # Eliminar el cliente
        db.session.delete(cliente)
        db.session.commit()
        flash('Cliente y sus ventas asociadas eliminados correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar cliente: {str(e)}', 'error')
        print(f"Error detallado: {str(e)}")  # Depuración

    return redirect(url_for('admin_routes.dashboard'))