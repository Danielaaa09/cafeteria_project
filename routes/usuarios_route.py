from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from app import db
from models.usuario import Usuario
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

usuarios_bp = Blueprint('usuarios', __name__)

# Crear usuario
@usuarios_bp.route('/usuarios', methods=['POST'])
def crear_usuario():
    data = request.get_json()
    hashed_password = generate_password_hash(data['contrasena'])

    nuevo_usuario = Usuario(
        nombre_completo=data['nombre_completo'],
        correo=data['correo'],
        telefono=data.get('telefono', ''),
        contrasena=hashed_password,
        rol=data['rol']
    )
    db.session.add(nuevo_usuario)
    db.session.commit()

    return jsonify({'mensaje': 'Usuario creado correctamente'}), 201

# Listar usuarios
@usuarios_bp.route('/usuarios', methods=['GET'])
def listar_usuarios():
    usuarios = Usuario.query.all()
    resultado = []
    for usuario in usuarios:
        resultado.append({
            'id': usuario.id,
            'nombre_completo': usuario.nombre_completo,
            'correo': usuario.correo,
            'telefono': usuario.telefono,
            'rol': usuario.rol,
            'fecha_creacion': usuario.fecha_creacion
        })
    return jsonify(resultado)

# Obtener usuario por ID
@usuarios_bp.route('/usuarios/<int:id>', methods=['GET'])
def obtener_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    return jsonify({
        'id': usuario.id,
        'nombre_completo': usuario.nombre_completo,
        'correo': usuario.correo,
        'telefono': usuario.telefono,
        'rol': usuario.rol,
        'fecha_creacion': usuario.fecha_creacion
    })

@usuarios_bp.route('/usuarios/<int:id>', methods=['PUT'])
def actualizar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    data = request.get_json()

    usuario.nombre_completo = data.get('nombre_completo', usuario.nombre_completo)
    usuario.correo = data.get('correo', usuario.correo)
    usuario.telefono = data.get('telefono', usuario.telefono)
    usuario.rol = data.get('rol', usuario.rol)

    db.session.commit()

    return jsonify({'mensaje': 'Usuario actualizado correctamente'})

@usuarios_bp.route('/usuarios/<int:id>', methods=['DELETE'])
def eliminar_usuario(id):
    usuario = Usuario.query.get_or_404(id)

    db.session.delete(usuario)
    db.session.commit()

    return jsonify({'mensaje': 'Usuario eliminado correctamente'})

@usuarios_bp.route('/anadir_empleado', methods=['GET', 'POST'])
def anadir_empleado():
    if request.method == 'POST':
        nombre = request.form['nombre_completo']
        correo = request.form['correo']
        telefono = request.form['telefono']
        nuevo_usuario = Usuario(
            nombre_completo=nombre,
            correo=correo,
            telefono=telefono,
            rol=2,  # O el rol que corresponda
            fecha_creacion=datetime.datetime.utcnow()
        )
        db.session.add(nuevo_usuario)
        db.session.commit()
        return redirect(url_for('usuarios_bp.anadir_empleado'))
    return render_template('admin/anadir_empleado.html')

@usuarios_bp.route('/editar_empleado/<int:id>', methods=['GET', 'POST'])
def editar_empleado(id):
    usuario = Usuario.query.get_or_404(id)
    if request.method == 'POST':
        usuario.nombre_completo = request.form['nombre_completo']
        usuario.correo = request.form['correo']
        usuario.telefono = request.form['telefono']
        db.session.commit()
        return redirect(url_for('usuarios_bp.editar_empleado', id=usuario.id))
    return render_template('admin/editar_empleado.html', usuario=usuario)
