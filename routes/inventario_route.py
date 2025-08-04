from flask import Blueprint, request, jsonify
from app import db
from models.inventario import Inventario

inventario_bp = Blueprint('inventario', __name__)

# Crear inventario
@inventario_bp.route('/inventario', methods=['POST'])
def crear_inventario():
    data = request.get_json()
    nuevo_inventario = Inventario(
        cantidad_disponible=data['cantidad_disponible'],
        cantidad_minima=data['cantidad_minima'],
        rotativo=data['rotativo'],
        producto_id=data['producto_id']
    )
    db.session.add(nuevo_inventario)
    db.session.commit()
    return jsonify({'mensaje': 'Inventario creado correctamente'}), 201

# Listar inventario
@inventario_bp.route('/inventario', methods=['GET'])
def listar_inventario():
    inventarios = Inventario.query.all()
    resultado = []
    for item in inventarios:
        resultado.append({
            'id': item.id,
            'cantidad_disponible': item.cantidad_disponible,
            'cantidad_minima': item.cantidad_minima,
            'fecha_actualizacion': item.fecha_actualizacion,
            'rotativo': item.rotativo,
            'producto_id': item.producto_id
        })
    return jsonify(resultado)

# Actualizar inventario
@inventario_bp.route('/inventario/<int:id>', methods=['PUT'])
def actualizar_inventario(id):
    item = Inventario.query.get_or_404(id)
    data = request.get_json()

    item.cantidad_disponible = data.get('cantidad_disponible', item.cantidad_disponible)
    item.cantidad_minima = data.get('cantidad_minima', item.cantidad_minima)
    item.rotativo = data.get('rotativo', item.rotativo)

    db.session.commit()
    return jsonify({'mensaje': 'Inventario actualizado correctamente'})

# Eliminar inventario
@inventario_bp.route('/inventario/<int:id>', methods=['DELETE'])
def eliminar_inventario(id):
    item = Inventario.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'mensaje': 'Inventario eliminado correctamente'})
