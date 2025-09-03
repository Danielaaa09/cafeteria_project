from flask import Blueprint, render_template, request, jsonify, session
from app import db
from models.producto import Producto
from models.mesa import Mesa
from models.orden import Orden
from models.detalle_orden import DetalleOrden
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime

empleados_routes = Blueprint("empleados_routes", __name__)

# Panel principal del mesero
@empleados_routes.route("/empleado")
def empleado_panel():
    mesas = Mesa.query.all()
    mesas_json = [{"id": m.id, "numero": m.numero, "estado": m.estado} for m in mesas]

    # Agrupar productos por categoría
    productos = Producto.query.all()
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
                continue
            producto_id = item["id"]
            producto = Producto.query.get(producto_id)
            if not producto:
                return jsonify({"success": False, "error": f"Producto con ID {producto_id} no encontrado"}), 404
            cantidad = max(1, int(item.get("cantidad", 1)))
            subtotal = producto.precio * cantidad
            total += subtotal

            detalle = DetalleOrden(
                orden_id=orden.id,
                producto_id=producto.id,
                cantidad=cantidad,
                subtotal=subtotal
            )
            db.session.add(detalle)

        if total == 0 and not productos:
            return jsonify({"success": False, "error": "No se agregaron productos"}), 400

        orden.total = total
        db.session.commit()

        return jsonify({"success": True, "orden_id": orden.id, "total": total})

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
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

        orden.estado = "pagada"
        orden.metodo_pago = metodo_pago
        orden.correo_cliente = correo_cliente

        mesa = Mesa.query.get(orden.mesa_id)
        mesa.estado = "disponible"

        # Generar y enviar factura PDF si se proporciona un correo
        if correo_cliente:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []

            elements.append(Paragraph("Cafetería Las Dos Amigas", styles['Title']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"Factura #{orden.id}", styles['Heading2']))
            elements.append(Paragraph(f"Cliente: {orden.correo_cliente.split('@')[0]}", styles['Normal']))
            elements.append(Paragraph(f"Fecha: {orden.fecha.strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            elements.append(Paragraph(f"Método de Pago: {metodo_pago}", styles['Normal']))
            elements.append(Spacer(1, 12))

            detalles = DetalleOrden.query.filter_by(orden_id=orden.id).all()
            data = [['Producto', 'Cantidad', 'Precio Unitario', 'Subtotal']]
            for detalle in detalles:
                data.append([
                    detalle.producto.nombre,
                    detalle.cantidad,
                    f"${detalle.subtotal / detalle.cantidad:.2f}",
                    f"${detalle.subtotal:.2f}"
                ])
            data.append(['Total', '', '', f"${orden.total:.2f}"])

            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.amber),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)

            doc.build(elements)
            buffer.seek(0)

            # Enviar correo con la factura
            remitente = 'cafeterialasdosamigas@gmail.com'
            password = 'doehmsrgujcalrrj'
            msg = MIMEMultipart()
            msg['From'] = remitente
            msg['To'] = correo_cliente
            msg['Subject'] = f'Factura #{orden.id} - Cafetería Las Dos Amigas'

            msg.attach(MIMEText(f"Adjunto encontrará su factura #{orden.id}. Gracias por su compra."))
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