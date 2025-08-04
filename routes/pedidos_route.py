from flask import Blueprint, request, jsonify
from app import db
from models.pedido_futuro import PedidoFuturo

pedidos_bp = Blueprint('pedidos', __name__)

# Crear pedido futuro
@pedidos_bp.route('/pedidos', methods=['POST'])
def crear_pedido():
    data = request.get_json()
    nuevo_pedido = PedidoFuturo(
        cantidad_pedida=data['cantidad_pedida'],
        fecha_pedido=data['fecha_pedido'],
        fecha_llegada=data['fecha_llegada'],
        precio_total=data['precio_total'],
        producto_id=data['producto_id']
    )
    db.session.add(nuevo_pedido)
    db.session.commit()
    return jsonify({'mensaje': 'Pedido futuro registrado correctamente'}), 201

# Listar pedidos
@pedidos_bp.route('/pedidos', methods=['GET'])
def listar_pedidos():
    pedidos = PedidoFuturo.query.all()
    resultado = []
    for pedido in pedidos:
        resultado.append({
            'id': pedido.id,
            'cantidad_pedida': pedido.cantidad_pedida,
            'fecha_pedido': pedido.fecha_pedido,
            'fecha_llegada': pedido.fecha_llegada,
            'precio_total': pedido.precio_total,
            'producto_id': pedido.producto_id
        })
    return jsonify(resultado)
