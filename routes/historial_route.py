from flask import Blueprint, request, jsonify
from app import db
from models.historial_inventario import HistorialInventario

historial_bp = Blueprint('historial', __name__)

# Crear historial
@historial_bp.route('/historial', methods=['POST'])
def crear_historial():
    data = request.get_json()
    nuevo_movimiento = HistorialInventario(
        tipo_movimiento=data['tipo_movimiento'],
        cantidad=data['cantidad'],
        descripcion=data.get('descripcion', ''),
        producto_id=data['producto_id']
    )
    db.session.add(nuevo_movimiento)
    db.session.commit()
    return jsonify({'mensaje': 'Movimiento registrado correctamente'}), 201

# Listar historial
@historial_bp.route('/historial', methods=['GET'])
def listar_historial():
    movimientos = HistorialInventario.query.all()
    resultado = []
    for mov in movimientos:
        resultado.append({
            'id': mov.id,
            'fecha_movimiento': mov.fecha_movimiento,
            'tipo_movimiento': mov.tipo_movimiento,
            'cantidad': mov.cantidad,
            'descripcion': mov.descripcion,
            'producto_id': mov.producto_id
        })
    return jsonify(resultado)
