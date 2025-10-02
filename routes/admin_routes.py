from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from models.usuario import Usuario
from models.categoria import Categoria
from models.producto import Producto
from models.venta import Venta
from models.detalle_venta import DetalleVenta
from models.orden import Orden
from models.detalle_orden import DetalleOrden
from app import db
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from werkzeug.utils import secure_filename
from datetime import date, datetime
from config import settings
from models.notificacion import Notificacion
import json

admin_routes = Blueprint('admin_routes', __name__)

# ---------------------------
# EMAIL
# ---------------------------
def enviar_correo(destinatario, asunto, cuerpo, nombre_completo=None):
    remitente = 'cafeterialasdosamigas@gmail.com'
    password = 'doehmsrgujcalrrj'

    mensaje = MIMEMultipart()
    mensaje['From'] = remitente
    mensaje['To'] = destinatario
    mensaje['Subject'] = asunto

    saludo = f"¡Hola {nombre_completo}!" if nombre_completo else "¡Hola!"
    cuerpo_completo = f"{saludo}\n\n{cuerpo}"
    mensaje.attach(MIMEText(cuerpo_completo, 'plain', 'utf-8'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(remitente, password)
            server.sendmail(remitente, destinatario, mensaje.as_string())
        print(f"Correo enviado correctamente a {destinatario}.")
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

    # Ventas totales hoy
    ventas_hoy = (db.session.query(db.func.sum(Venta.total)).filter(db.func.date(Venta.fecha) == hoy).scalar()) or 0
    ordenes_hoy = (db.session.query(db.func.sum(Orden.total)).filter(db.func.date(Orden.fecha_creacion) == hoy).scalar()) or 0
    total_hoy = ventas_hoy + ordenes_hoy

    # Pedidos totales hoy
    pedidos_ventas = db.session.query(Venta).filter(db.func.date(Venta.fecha) == hoy).count()
    pedidos_ordenes = db.session.query(Orden).filter(db.func.date(Orden.fecha_creacion) == hoy).count()
    pedidos = pedidos_ventas + pedidos_ordenes

    # Desglose por método de pago
    ventas_efectivo = (db.session.query(db.func.sum(Venta.total)).filter(db.func.date(Venta.fecha) == hoy, Venta.metodo_pago == 'Efectivo').scalar()) or 0
    ventas_tarjeta = (db.session.query(db.func.sum(Venta.total)).filter(db.func.date(Venta.fecha) == hoy, Venta.metodo_pago == 'Tarjeta').scalar()) or 0
    ventas_transferencia = (db.session.query(db.func.sum(Venta.total)).filter(db.func.date(Venta.fecha) == hoy, Venta.metodo_pago == 'Transferencia').scalar()) or 0

    # Historial de ventas por día
    fechas_ventas = db.session.query(db.func.date(Venta.fecha).label('fecha')).distinct().all()
    fechas_ordenes = db.session.query(db.func.date(Orden.fecha_creacion).label('fecha')).distinct().all()
    fechas = sorted(set([f.fecha for f in fechas_ventas] + [f.fecha for f in fechas_ordenes]), reverse=True)
    sales_history = []

    for fecha in fechas:
        total_ventas = (db.session.query(db.func.sum(Venta.total)).filter(db.func.date(Venta.fecha) == fecha).scalar()) or 0
        total_ordenes = (db.session.query(db.func.sum(Orden.total)).filter(db.func.date(Orden.fecha_creacion) == fecha).scalar()) or 0
        efectivo = (db.session.query(db.func.sum(Venta.total)).filter(db.func.date(Venta.fecha) == fecha, Venta.metodo_pago == 'Efectivo').scalar()) or 0
        tarjeta = (db.session.query(db.func.sum(Venta.total)).filter(db.func.date(Venta.fecha) == fecha, Venta.metodo_pago == 'Tarjeta').scalar()) or 0
        transferencia = (db.session.query(db.func.sum(Venta.total)).filter(db.func.date(Venta.fecha) == fecha, Venta.metodo_pago == 'Transferencia').scalar()) or 0

        sales_history.append({
            'date': fecha.strftime('%Y-%m-%d'),
            'total': total_ventas + total_ordenes,
            'efectivo': efectivo,
            'tarjeta': tarjeta,
            'transferencia': transferencia
        })

    productos_bajo_stock = [p for p in productos if p.cantidad <= 10]
    notificaciones = Notificacion.query.order_by(Notificacion.fecha.desc()).limit(10).all()

    # Procesar datos JSON para notificaciones
    for n in notificaciones:
        try:
            n.datos_dict = json.loads(n.datos) if n.datos else {}
        except Exception:
            n.datos_dict = {}

    # Obtener lista de pedidos (Ventas y Ordenes)
    pedidos_list = []
    # Ventas
    ventas = Venta.query.all()
    for venta in ventas:
        cliente = Usuario.query.get(venta.usuarios_id)
        detalles = DetalleVenta.query.filter_by(venta_id=venta.id).all()
        productos = [Producto.query.get(d.producto_id).nombre for d in detalles]
        pedidos_list.append({
            'id': venta.id,
            'tipo': 'venta',
            'cliente': cliente.nombre_completo if cliente else 'Desconocido',
            'cantidad': sum(d.cantidad for d in detalles),
            'productos': productos,
            'direccion': cliente.direccion if cliente else 'N/A',
            'telefono': cliente.telefono if cliente else 'N/A',
            'estado': venta.estado or 'pendiente',
            'total': venta.total,
            'fecha': venta.fecha.strftime('%Y-%m-%d %H:%M:%S')
        })
    # Ordenes
    ordenes = Orden.query.all()
    for orden in ordenes:
        cliente = Usuario.query.filter_by(correo=orden.correo_cliente).first()
        detalles = DetalleOrden.query.filter_by(orden_id=orden.id).all()
        productos = [Producto.query.get(d.producto_id).nombre for d in detalles]
        pedidos_list.append({
            'id': orden.id,
            'tipo': 'orden',
            'cliente': cliente.nombre_completo if cliente else orden.correo_cliente or 'Desconocido',
            'productos': productos,
            'direccion': cliente.direccion if cliente else 'N/A',
            'telefono': cliente.telefono if cliente else 'N/A',
            'estado': orden.estado or 'pendiente',
            'total': orden.total,
            'fecha': orden.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S')
        })

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
        ventas_hoy=total_hoy,
        pedidos=pedidos,
        ventas_efectivo=ventas_efectivo,
        ventas_tarjeta=ventas_tarjeta,
        ventas_transferencia=ventas_transferencia,
        productos_bajo_stock=productos_bajo_stock,
        sales_history=sales_history,
        notificaciones=notificaciones,
        pedidos_list=pedidos_list
    )

# ---------------------------
# NOTIFICACIONES
# ---------------------------
@admin_routes.route('/marcar_notificacion_leida/<int:id>', methods=['POST'])
def marcar_notificacion_leida(id):
    notificacion = Notificacion.query.get_or_404(id)
    try:
        db.session.delete(notificacion)
        db.session.commit()
        flash('Notificación marcada como leída.', 'success')
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        flash(f'Error al marcar notificación: {str(e)}', 'error')
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ---------------------------
# PEDIDOS
# ---------------------------
@admin_routes.route('/actualizar_estado_pedido/<int:id>', methods=['POST'])
def actualizar_estado_pedido(id):
    estado = request.form.get('estado')
    tipo = request.form.get('tipo')
    valid_states = ['pendiente', 'enviado', 'en camino', 'entregado']

    if estado not in valid_states:
        flash('Estado inválido.', 'error')
        return redirect(url_for('admin_routes.dashboard'))

    try:
        if tipo == 'venta':
            pedido = Venta.query.get_or_404(id)
            cliente = Usuario.query.get(pedido.usuarios_id)
            fecha = pedido.fecha
        elif tipo == 'orden':
            pedido = Orden.query.get_or_404(id)
            cliente = Usuario.query.filter_by(correo=pedido.correo_cliente).first()
            fecha = pedido.fecha_creacion
        else:
            flash('Tipo de pedido inválido.', 'error')
            return redirect(url_for('admin_routes.dashboard'))

        pedido.estado = estado
        db.session.commit()

        # Enviar correo al cliente
        if cliente and cliente.correo:
            asunto = f"Actualización del estado de tu pedido #{id} ({tipo})"
            cuerpo = f"Tu pedido #{id} ({tipo}) ha sido actualizado al estado: {estado.capitalize()}.\n\nDetalles del pedido:\n- Fecha: {fecha.strftime('%Y-%m-%d %H:%M:%S')}\n- Total: ${pedido.total:.2f}"
            enviar_correo(cliente.correo, asunto, cuerpo, cliente.nombre_completo)

        flash(f'Estado del pedido actualizado a {estado}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar estado: {str(e)}', 'error')

    return redirect(url_for('admin_routes.dashboard'))

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

            if cantidad <= 10:
                notificacion = Notificacion(
                    mensaje=f"El producto {nombre} tiene bajo stock ({cantidad} unidades).",
                    tipo='bajo_stock',
                    datos=json.dumps({'producto_id': nuevo_producto.id, 'nombre': nombre, 'cantidad': cantidad}),
                    fecha=datetime.now()
                )
                db.session.add(notificacion)
                db.session.commit()
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

    imagen = request.files.get('imagen')
    if imagen and imagen.filename != "":
        try:
            filename = secure_filename(imagen.filename)
            carpeta_destino = os.path.join('static', 'img')
            os.makedirs(carpeta_destino, exist_ok=True)
            ruta = os.path.join(carpeta_destino, filename)
            imagen.save(ruta)
            producto.imagen_url = f'/static/img/{filename}'
        except Exception as e:
            flash(f'Error al guardar la imagen: {str(e)}', 'error')
            return redirect(url_for('admin_routes.dashboard'))

    try:
        db.session.commit()
        flash('Producto actualizado correctamente.', 'success')

        notificacion_existente = Notificacion.query.filter_by(tipo='bajo_stock', datos=json.dumps({'producto_id': producto.id})).first()
        if producto.cantidad <= 10:
            if not notificacion_existente:
                notificacion = Notificacion(
                    mensaje=f"El producto {producto.nombre} tiene bajo stock ({producto.cantidad} unidades).",
                    tipo='bajo_stock',
                    datos=json.dumps({'producto_id': producto.id, 'nombre': producto.nombre, 'cantidad': producto.cantidad}),
                    fecha=datetime.now()
                )
                db.session.add(notificacion)
                db.session.commit()
        elif notificacion_existente:
            db.session.delete(notificacion_existente)
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar producto: {str(e)}', 'error')

    return redirect(url_for('admin_routes.dashboard'))

@admin_routes.route('/eliminar_producto/<int:id>', methods=['POST'])
def eliminar_producto(id):
    producto = Producto.query.get_or_404(id)
    try:
        DetalleVenta.query.filter_by(producto_id=producto.id).delete(synchronize_session='fetch')
        DetalleOrden.query.filter_by(producto_id=producto.id).delete(synchronize_session='fetch')
        notificacion = Notificacion.query.filter_by(tipo='bajo_stock', datos=json.dumps({'producto_id': producto.id})).first()
        if notificacion:
            db.session.delete(notificacion)
        db.session.delete(producto)
        db.session.commit()
        flash('Producto y sus detalles asociados eliminados correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar producto: {str(e)}', 'error')
        print(f"Error detallado: {str(e)}")

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

    if enviar_correo(correo, 'Tu nueva contraseña temporal', f"Tu nueva contraseña temporal es: {contrasena_temporal}\n\nPor favor cámbiala después de iniciar sesión.", nombre_completo=nombre):
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

    if enviar_correo(correo, 'Tu nueva contraseña temporal', f"Tu nueva contraseña temporal es: {contrasena_temporal}\n\nPor favor cámbiala después de iniciar sesión.", nombre_completo=nombre):
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
        ventas = Venta.query.filter_by(usuarios_id=cliente.id).all()
        for venta in ventas:
            DetalleVenta.query.filter_by(venta_id=venta.id).delete(synchronize_session='fetch')
            db.session.delete(venta)
        ordenes = Orden.query.filter_by(correo_cliente=cliente.correo).all()
        for orden in ordenes:
            DetalleOrden.query.filter_by(orden_id=orden.id).delete(synchronize_session='fetch')
            db.session.delete(orden)
        db.session.delete(cliente)
        db.session.commit()
        flash('Cliente y sus pedidos asociados eliminados correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar cliente: {str(e)}', 'error')
        print(f"Error detallado: {str(e)}")

    return redirect(url_for('admin_routes.dashboard'))