import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from app import db
from models.producto import Producto

productos_bp = Blueprint('productos', __name__)

# Crear producto con imagen
@productos_bp.route('/productos', methods=['POST'])
def crear_producto():
    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion', '')
    precio = request.form.get('precio')
    es_rotativo = request.form.get('es_rotativo', False)
    categorias_id = request.form.get('categorias_id')
    imagen = request.files.get('imagen')

    imagen_url = None
    if imagen and imagen.filename != '':
        filename = secure_filename(imagen.filename)
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        ruta = os.path.join(upload_folder, filename)
        imagen.save(ruta)
        imagen_url = f'/static/uploads/{filename}'

    nuevo_producto = Producto(
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        es_rotativo=es_rotativo,
        categorias_id=categorias_id,
        imagen_url=imagen_url
    )
    db.session.add(nuevo_producto)
    db.session.commit()
    return jsonify({'mensaje': 'Producto creado correctamente'}), 201

# Listar productos (incluyendo imagen_url)
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
            'categorias_id': producto.categorias_id,
            'imagen_url': producto.imagen_url
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
