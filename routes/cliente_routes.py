from flask import Blueprint, render_template, session, request, jsonify, redirect, url_for, flash
from models.producto import Producto
from models.usuario import Usuario   
from models.venta import Venta
from models.detalle_venta import DetalleVenta
import datetime
from app import db
from flask import make_response
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
from models.categoria import Categoria

cliente_routes = Blueprint('cliente_routes', __name__)

@cliente_routes.route('/cliente')
def index():
    categorias = Categoria.query.all()
    usuario = None
    if 'user_id' in session:
        usuario = Usuario.query.get(session['user_id'])
    return render_template('cliente.html', categorias=categorias, usuario=usuario)
    
@cliente_routes.route('/checkout', methods=['POST'])
def checkout():
    if 'user_id' not in session:
        return jsonify({'error': 'Debes iniciar sesión para comprar'}), 403
    try:
        data = request.json
        carrito = data.get('carrito', [])
        metodo_pago = data.get('metodo_pago', 'Efectivo')
        if not carrito:
            return jsonify({'error': 'El carrito está vacío'}), 400
        total = sum(float(item['precio']) * int(item['cantidad']) for item in carrito)
        venta = Venta(
            usuarios_id=session['user_id'],
            fecha=datetime.datetime.utcnow(),
            total=total,
            metodo_pago=metodo_pago
        )
        db.session.add(venta)
        db.session.commit()
        for item in carrito:
            producto = Producto.query.get(item['id'])
            if not producto:
                return jsonify({'error': f'Producto con ID {item["id"]} no encontrado'}), 404
            detalle = DetalleVenta(
                venta_id=venta.id,
                producto_id=producto.id,
                cantidad=int(item['cantidad']),
                subtotal=float(item['precio']) * int(item['cantidad'])
            )
            db.session.add(detalle)
        db.session.commit()
        return jsonify({'message': 'Compra realizada con éxito', 'venta_id': venta.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@cliente_routes.route('/factura/<int:venta_id>')
def factura_pdf(venta_id):
        try:
            venta = Venta.query.get_or_404(venta_id)
            detalles = DetalleVenta.query.filter_by(venta_id=venta.id).all()
            usuario = Usuario.query.get(venta.usuarios_id)
            if not usuario:
                return jsonify({'error': 'Usuario no encontrado'}), 404
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            p.setFillColorRGB(0.87, 0.68, 0.21)
            p.setFont("Helvetica-Bold", 24)
            p.drawString(200, height - 60, "Cafetería Las Dos Amigas")
            p.line(50, height - 70, width - 50, height - 70)
            p.setFillColorRGB(0, 0, 0)
            p.setFont("Helvetica", 10)
            p.drawString(50, height - 90, "Factura N° " + str(venta.id))
            p.setFont("Helvetica-Bold", 12)
            p.drawString(50, height - 120, "Detalles de la Factura")
            p.setFont("Helvetica", 10)
            p.drawString(50, height - 140, f"Cliente: {usuario.nombre_completo}")
            p.drawString(50, height - 160, f"Correo: {usuario.correo}")
            p.drawString(50, height - 180, f"Fecha: {venta.fecha.strftime('%d/%m/%Y %H:%M')}")
            p.drawString(50, height - 200, f"Dirección: {usuario.direccion}")
            p.drawString(50, height - 220, f"Método de Pago: {venta.metodo_pago}")
            y = height - 240
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
            for detalle in detalles:
                producto = detalle.producto
                if not producto:
                    return jsonify({'error': f'Producto no encontrado para detalle {detalle.id}'}), 404
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
                p.drawString(350, y, f"${producto.precio:.2f}")
                p.drawString(450, y, f"${detalle.subtotal:.2f}")
            y -= 30
            p.setFillColorRGB(0.87, 0.68, 0.21)
            p.rect(350, y, 200, 20, fill=True, stroke=False)
            p.setFillColorRGB(1, 1, 1)
            p.setFont("Helvetica-Bold", 12)
            p.drawString(350, y + 5, "TOTAL:")
            p.drawString(450, y + 5, f"${venta.total:.2f}")
            p.setFillColorRGB(0, 0, 0)
            y -= 40
            p.setFont("Helvetica-Oblique", 10)
            p.setFillColorRGB(0.4, 0.4, 0.4)
            p.drawString(200, y, "¡Gracias por tu compra en Cafetería Las Dos Amigas!")
            p.setFillColorRGB(0, 0, 0)
            p.showPage()
            p.save()
            buffer.seek(0)
            response = make_response(buffer.getvalue())
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'inline; filename=factura_{venta.id}.pdf'
            return response
        except Exception as e:
            return jsonify({'error': f'Error al generar la factura: {str(e)}'}), 500
    
@cliente_routes.route('/obtener_historial', methods=['GET'])
def obtener_historial():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Debes iniciar sesión para ver el historial'}), 403
        usuario_id = session['user_id']
        ventas = Venta.query.filter_by(usuarios_id=usuario_id).order_by(Venta.fecha.desc()).all()
        if not ventas:
            return jsonify({'error': 'No se encontraron compras'}), 404
        historial = []
        for venta in ventas:
            detalles = DetalleVenta.query.filter_by(venta_id=venta.id).all()
            historial.append({
                'id': venta.id,
                'fecha': venta.fecha.strftime('%d/%m/%Y %H:%M'),
                'total': float(venta.total),
                'metodo_pago': venta.metodo_pago,
                'detalles': [{'nombre': d.producto.nombre, 'cantidad': d.cantidad, 'subtotal': float(d.subtotal)} for d in detalles]
            })
        return jsonify({'historial': historial})
    except Exception as e:
        return jsonify({'error': f'Error al obtener el historial: {str(e)}'}), 500
    
@cliente_routes.route('/editar_perfil')
def editar_perfil():
    if 'user_id' not in session:
        return jsonify({'error': 'Debes iniciar sesión para editar el perfil'}), 403
    usuario = Usuario.query.get(session['user_id'])
    return jsonify({
        'nombre_completo': usuario.nombre_completo,
        'telefono': usuario.telefono,
        'correo': usuario.correo,
        'direccion': usuario.direccion
    })

@cliente_routes.route('/actualizar_perfil', methods=['POST'])
def actualizar_perfil():
    if 'user_id' not in session:
        return jsonify({'error': 'Debes iniciar sesión para actualizar el perfil'}), 403
    try:
        usuario = Usuario.query.get(session['user_id'])
        usuario.nombre_completo = request.form['nombre_completo']
        usuario.telefono = request.form['telefono']
        usuario.correo = request.form['correo']
        usuario.direccion = request.form['direccion']
        db.session.commit()
        return jsonify({'message': 'Perfil actualizado con éxito'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar el perfil: {str(e)}'}), 500