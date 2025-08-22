# routes/cliente_routes.py
from flask import Blueprint, render_template, session, request, jsonify
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

cliente_routes = Blueprint('cliente_routes', __name__)

@cliente_routes.route('/cliente')
def panel_cliente():
    productos = Producto.query.all()

    usuario = None
    if 'user_id' in session:
        usuario = Usuario.query.get(session['user_id'])

    return render_template('cliente.html', productos=productos, usuario=usuario)

@cliente_routes.route('/checkout', methods=['POST'])
def checkout():
    if 'user_id' not in session:
        return jsonify({'error': 'Debes iniciar sesión para comprar'}), 403

    data = request.json
    carrito = data.get('carrito', [])
    total = sum(item['precio'] * item['cantidad'] for item in carrito)

    # Crear venta
    venta = Venta(
    usuarios_id=session['user_id'],
    fecha_venta=datetime.datetime.utcnow(),
    total=total
)

    db.session.add(venta)
    db.session.commit()

    # Agregar detalles de venta
    for item in carrito:
        producto = Producto.query.get(item['id'])
        detalle = DetalleVenta(
            venta_id=venta.id,
            producto_id=producto.id,
            cantidad=item['cantidad'],
            subtotal=item['precio'] * item['cantidad']
        )
        db.session.add(detalle)

    db.session.commit()

    return jsonify({'message': 'Compra realizada con éxito', 'venta_id': venta.id})
@cliente_routes.route('/factura/<int:venta_id>')
def factura_pdf(venta_id):
    venta = Venta.query.get_or_404(venta_id)
    detalles = DetalleVenta.query.filter_by(venta_id=venta.id).all()
    
    # 🔹 Obtener el usuario a partir del FK
    usuario = Usuario.query.get(venta.usuarios_id)

    # Crear buffer en memoria
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Encabezado
    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, height - 50, "Cafetería Las Dos Amigas")
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 80, f"Factura N° {venta.id}")
    p.drawString(50, height - 100, f"Cliente: {usuario.nombre_completo}")
    p.drawString(50, height - 120, f"Correo: {usuario.correo}")
    p.drawString(50, height - 140, f"Fecha: {venta.fecha_venta.strftime('%d/%m/%Y %H:%M')}")

    # Tabla de productos
    y = height - 180
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Producto")
    p.drawString(250, y, "Cantidad")
    p.drawString(350, y, "Precio")
    p.drawString(450, y, "Subtotal")
    y -= 20
    p.setFont("Helvetica", 12)

    for detalle in detalles:
        producto = detalle.producto
        p.drawString(50, y, producto.nombre)
        p.drawString(250, y, str(detalle.cantidad))
        p.drawString(350, y, f"${producto.precio:.2f}")
        p.drawString(450, y, f"${detalle.subtotal:.2f}")
        y -= 20

    # Total
    y -= 20
    p.setFont("Helvetica-Bold", 12)
    p.drawString(350, y, "TOTAL:")
    p.drawString(450, y, f"${venta.total:.2f}")

    # Footer
    y -= 40
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(200, y, "¡Gracias por tu compra!")

    # Guardar PDF en buffer
    p.showPage()
    p.save()
    buffer.seek(0)

    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=factura_{venta.id}.pdf'
    return response
