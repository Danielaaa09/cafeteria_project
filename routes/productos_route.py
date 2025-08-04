from flask import Blueprint, request, jsonify
from app import db
from models.producto import Producto

productos_bp = Blueprint('productos', __name__)

# Crear producto
@productos_bp.route('/productos', methods=['POST'])
def crear_producto():
    data = request.get_json()
    nuevo_producto = Producto(
        nombre=data['nombre'],
        descripcion=data.get('descripcion', ''),
        precio=data['precio'],
        es_rotativo=data['es_rotativo'],
        categorias_id=data['categorias_id']
    )
    db.session.add(nuevo_producto)
    db.session.commit()
    return jsonify({'mensaje': 'Producto creado correctamente'}), 201

# Listar productos
@productos_bp.route('/productos', methods=['GET'])
def listar_productos():
    productos = Producto.query.all()
    resultado = []
    for producto in productos:
        resultado.append({
            'id': producto.id,
            'nombre': producto.nombre,
            'descripcion': producto.descripcion,
            'precio': producto.precio,
            'es_rotativo': producto.es_rotativo,
            'categorias_id': producto.categorias_id
        })
    return jsonify(resultado)

# Actualizar producto
@productos_bp.route('/productos/<int:id>', methods=['PUT'])
def actualizar_producto(id):
    producto = Producto.query.get_or_404(id)
    data = request.get_json()

    producto.nombre = data.get('nombre', producto.nombre)
    producto.descripcion = data.get('descripcion', producto.descripcion)
    producto.precio = data.get('precio', producto.precio)
    producto.es_rotativo = data.get('es_rotativo', producto.es_rotativo)
    producto.categorias_id = data.get('categorias_id', producto.categorias_id)

    db.session.commit()
    return jsonify({'mensaje': 'Producto actualizado correctamente'})

# Eliminar producto
@productos_bp.route('/productos/<int:id>', methods=['DELETE'])
def eliminar_producto(id):
    producto = Producto.query.get_or_404(id)
    db.session.delete(producto)
    db.session.commit()
    return jsonify({'mensaje': 'Producto eliminado correctamente'})
