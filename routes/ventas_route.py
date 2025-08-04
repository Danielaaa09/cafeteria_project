from flask import Blueprint, request, jsonify
from app import db
from models.venta import Venta
from models.detalle_venta import DetalleVenta

ventas_bp = Blueprint('ventas', __name__)

# Crear venta
@ventas_bp.route('/ventas', methods=['POST'])
def crear_venta():
    data = request.get_json()
    nueva_venta = Venta(
        total=data['total'],
        usuarios_id=data['usuarios_id']
    )
    db.session.add(nueva_venta)
    db.session.commit()

    # Guardar detalles de venta
    for detalle in data['detalles']:
        nuevo_detalle = DetalleVenta(
            cantidad=detalle['cantidad'],
            precio_unitario=detalle['precio_unitario'],
            subtotal=detalle['subtotal'],
            ventas_id=nueva_venta.id,
            producto_id=detalle['producto_id']
        )
        db.session.add(nuevo_detalle)

    db.session.commit()
    return jsonify({'mensaje': 'Venta creada correctamente'}), 201

# Listar ventas
@ventas_bp.route('/ventas', methods=['GET'])
def listar_ventas():
    ventas = Venta.query.all()
    resultado = []
    for venta in ventas:
        resultado.append({
            'id': venta.id,
            'fecha_venta': venta.fecha_venta,
            'total': venta.total,
            'usuarios_id': venta.usuarios_id
        })
    return jsonify(resultado)
