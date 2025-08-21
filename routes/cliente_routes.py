# routes/cliente_routes.py
from flask import Blueprint, render_template, session
from models.producto import Producto
from models.usuario import Usuario   

cliente_routes = Blueprint('cliente_routes', __name__)

@cliente_routes.route('/cliente')
def panel_cliente():
    productos = Producto.query.all()

    usuario = None
    if 'user_id' in session:
        usuario = Usuario.query.get(session['user_id'])

    return render_template('cliente.html', productos=productos, usuario=usuario)
