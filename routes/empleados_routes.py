from flask import Blueprint, render_template, request, jsonify, session
from app import db
from models.producto import Producto
from models.mesa import Mesa
from models.orden import Orden
from models.detalle_orden import DetalleOrden
from models.notificacion import Notificacion
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
import json

empleados_routes = Blueprint("empleados_routes", __name__)

# Panel principal del mesero
@empleados_routes.route("/empleado")
def empleado_panel():
    mesas = Mesa.query.all()
    mesas_json = [{"id": m.id, "numero": m.numero, "estado": m.estado} for m in mesas]

    # Agrupar productos por categoría
    productos = Producto.query.filter(Producto.cantidad > 0).all()
    productos_por_categoria = {}
    for p in productos:
        categoria_nombre = p.categoria.nombre if p.categoria else "Sin categoría"
        if categoria_nombre not in productos_por_categoria:
            productos_por_categoria[categoria_nombre] = []
        productos_por_categoria[categoria_nombre].append({
            "id": p.id,
            "nombre": p.nombre,
            "precio": float(p.precio)
        })

    ordenes = Orden.query.filter_by(estado="pendiente").all()
    ordenes_json = [
        {"id": o.id, "mesa_id": o.mesa_id, "total": float(o.total), "estado": o.estado}
        for o in ordenes
    ]

    return render_template(
        "empleado.html",
        mesas_json=mesas_json,
        productos_por_categoria=productos_por_categoria,
        ordenes_json=ordenes_json,
        nombre_mesero=session.get('nombre_completo')
    )

# Crear una nueva orden
@empleados_routes.route("/empleado/orden/nueva", methods=["POST"], endpoint="nueva_orden_unique")
def nueva_orden():
    try:
        data = request.get_json()
        print(f"Datos recibidos: {data}")  # Depuración
        if not data or "mesa_id" not in data or not data.get("productos"):
            return jsonify({"success": False, "error": "Datos incompletos"}), 400

        mesa_id = data.get("mesa_id")
        productos = data.get("productos", [])

        if not isinstance(mesa_id, int):
            return jsonify({"success": False, "error": "ID de mesa inválido"}), 400

        mesa = Mesa.query.get(mesa_id)
        if not mesa:
            return jsonify({"success": False, "error": f"Mesa con ID {mesa_id} no encontrada"}), 404

        mesa.estado = "ocupada"
        orden = Orden(mesa_id=mesa_id, estado="pendiente", total=0)
        db.session.add(orden)
        db.session.flush()

        total = 0
        for item in productos:
            if not isinstance(item, dict) or "id" not in item or "cantidad" not in item:
                print(f"Producto inválido ignorado: {item}")
                continue
            producto_id = item["id"]
            producto = Producto.query.get(producto_id)
            if not producto:
                return jsonify({"success": False, "error": f"Producto con ID {producto_id} no encontrado"}), 404
            print(f"Producto cargado - Atributos antes: {producto.__dict__}")  # Depuración antes
            # Verifica y asigna el precio
            if hasattr(producto, 'precio') and producto.precio is not None:
                precio_unitario = float(producto.precio)
                print(f"Precio encontrado: {precio_unitario}")  # Depuración
            elif hasattr(producto, 'precio_unitario') and producto.precio_unitario is not None:
                precio_unitario = float(producto.precio_unitario)
                print(f"Precio_unitario encontrado: {precio_unitario}")  # Depuración
            else:
                return jsonify({"success": False, "error": f"Campo de precio no encontrado o nulo para producto ID {producto_id}"}), 400
            print(f"Producto cargado - Atributos después: {producto.__dict__}")  # Depuración después
            cantidad = max(1, int(item.get("cantidad", 1)))
            subtotal = precio_unitario * cantidad
            total += subtotal

            detalle = DetalleOrden(
                orden_id=orden.id,
                producto_id=producto.id,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                subtotal=subtotal
            )
            db.session.add(detalle)
            # --- ACTUALIZAR STOCK Y NOTIFICAR ---
            producto.cantidad -= cantidad
            if producto.cantidad < 0:
                producto.cantidad = 0
            # Notificación de stock bajo
            if producto.cantidad <= 5:
                mensaje = f"Stock bajo para {producto.nombre}: quedan {producto.cantidad} unidades."
                datos = {
                    "producto": producto.nombre,
                    "cantidad": producto.cantidad
                }
                notificacion = Notificacion(
                    mensaje=mensaje,
                    tipo='stock_bajo',
                    datos=json.dumps(datos)
                )
                db.session.add(notificacion)
            print(f"Detalle creado: orden_id={orden.id}, producto_id={producto_id}, cantidad={cantidad}, precio_unitario={precio_unitario}, subtotal={subtotal}")

        if total == 0 and not productos:
            return jsonify({"success": False, "error": "No se agregaron productos"}), 400

        orden.total = total
        db.session.commit()

        return jsonify({"success": True, "orden_id": orden.id, "total": total})

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        print(f"Error details: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# Finalizar orden (pagar) y enviar factura
@empleados_routes.route("/empleado/orden/<int:orden_id>/pagar", methods=["POST"])
def pagar_orden(orden_id):
    try:
        data = request.get_json()
        metodo_pago = data.get("metodo_pago")
        correo_cliente = data.get("correo_cliente")

        orden = Orden.query.get(orden_id)
        if not orden or orden.estado != "pendiente":
            return jsonify({"success": False, "error": "Orden no válida"}), 400

        orden.estado = "pagado"
        orden.metodo_pago = metodo_pago
        orden.correo_cliente = correo_cliente

        mesa = Mesa.query.get(orden.mesa_id)
        mesa.estado = "disponible"

        # Generar y enviar factura PDF si se proporciona un correo
        if correo_cliente:
            buffer = BytesIO()
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            width, height = letter
            p = canvas.Canvas(buffer, pagesize=letter)
            # Encabezado
            p.setFillColorRGB(0.87, 0.68, 0.21)
            p.setFont("Helvetica-Bold", 24)
            p.drawString(200, height - 60, "Cafetería Las Dos Amigas")
            p.line(50, height - 70, width - 50, height - 70)
            p.setFillColorRGB(0, 0, 0)
            p.setFont("Helvetica", 10)
            p.drawString(50, height - 90, "Factura N° " + str(orden.id))
            p.setFont("Helvetica-Bold", 12)
            p.drawString(50, height - 120, "Detalles de la Factura")
            p.setFont("Helvetica", 10)
            p.drawString(50, height - 140, f"Cliente: {orden.correo_cliente.split('@')[0]}")
            p.drawString(50, height - 160, f"Fecha: {orden.fecha_creacion.strftime('%d/%m/%Y %H:%M')}")
            p.drawString(50, height - 180, f"Método de Pago: {metodo_pago}")
            y = height - 200
            p.setFont("Helvetica-Bold", 10)
            p.drawString(50, y, "Producto")
            p.drawString(250, y, "Cantidad")
            p.drawString(350, y, "Precio Unit.")
            p.drawString(450, y, "Subtotal")
            y -= 20
            p.setFillColorRGB(0.95, 0.95, 0.95)
            p.rect(50, y, 500, 20, fill=True, stroke=False)
            p.setFillColorRGB(0, 0, 0)
            p.setFont("Helvetica", 10)
            detalles = DetalleOrden.query.filter_by(orden_id=orden.id).all()
            for detalle in detalles:
                producto = detalle.producto
                y -= 20
                if y < 50:
                    p.showPage()
                    y = height - 60
                    p.setFont("Helvetica-Bold", 10)
                    p.drawString(50, y, "Producto")
                    p.drawString(250, y, "Cantidad")
                    p.drawString(350, y, "Precio Unit.")
                    p.drawString(450, y, "Subtotal")
                    y -= 20
                    p.setFillColorRGB(0.95, 0.95, 0.95)
                    p.rect(50, y, 500, 20, fill=True, stroke=False)
                    p.setFillColorRGB(0, 0, 0)
                p.drawString(50, y, producto.nombre)
                p.drawString(250, y, str(detalle.cantidad))
                p.drawString(350, y, f"${detalle.subtotal / detalle.cantidad:.2f}")
                p.drawString(450, y, f"${detalle.subtotal:.2f}")
            y -= 30
            p.setFillColorRGB(0.87, 0.68, 0.21)
            p.rect(350, y, 200, 20, fill=True, stroke=False)
            p.setFillColorRGB(1, 1, 1)
            p.setFont("Helvetica-Bold", 12)
            p.drawString(350, y + 5, "TOTAL:")
            p.drawString(450, y + 5, f"${orden.total:.2f}")
            p.setFillColorRGB(0, 0, 0)
            y -= 40
            p.setFont("Helvetica-Oblique", 10)
            p.setFillColorRGB(0.4, 0.4, 0.4)
            p.drawString(200, y, "¡Gracias por tu compra en Cafetería Las Dos Amigas!")
            p.setFillColorRGB(0, 0, 0)
            p.showPage()
            p.save()
            buffer.seek(0)

            # Enviar correo con la factura
            remitente = 'cafeterialasdosamigas@gmail.com'
            password = 'doehmsrgujcalrrj'
            msg = MIMEMultipart()
            msg['From'] = remitente
            msg['To'] = correo_cliente
            msg['Subject'] = f'Factura #{orden.id} - Cafetería Las Dos Amigas'

            msg.attach(MIMEText(f"Adjunto encontrará su factura #{orden.id}. Gracias por su compra.", 'plain'))
            with buffer as attachment:
                part = MIMEApplication(attachment.read(), Name=f"factura_{orden.id}.pdf")
                part['Content-Disposition'] = f'attachment; filename="factura_{orden.id}.pdf"'
                msg.attach(part)

            try:
                with smtplib.SMTP('smtp.gmail.com', 587) as server:
                    server.starttls()
                    server.login(remitente, password)
                    server.sendmail(remitente, correo_cliente, msg.as_string())
            except Exception as e:
                print(f"Error al enviar correo: {e}")  # Solo log, no interrumpe

        db.session.commit()
        return jsonify({"success": True, "mensaje": "Orden pagada con éxito, factura enviada si se proporcionó correo"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@empleados_routes.route("/empleado/orden/<int:orden_id>/detalles", methods=["GET"])
def obtener_detalles_orden(orden_id):
    try:
        orden = Orden.query.get(orden_id)
        if not orden or orden.estado != "pendiente":
            return jsonify({"success": False, "error": "Orden no válida"}), 400

        detalles = DetalleOrden.query.filter_by(orden_id=orden_id).all()
        productos = [
            {
                "id": detalle.producto_id,
                "nombre": detalle.producto.nombre,
                "precio": float(detalle.subtotal / detalle.cantidad),
                "cantidad": detalle.cantidad,
                "subtotal": float(detalle.subtotal)
            }
            for detalle in detalles
        ]

        return jsonify({
            "success": True,
            "orden": {
                "id": orden.id,
                "mesa_id": orden.mesa_id,
                "total": float(orden.total),
                "productos": productos
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500