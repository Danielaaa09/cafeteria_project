# Ejemplo en tu routes/cliente_routes.py
from flask import Blueprint, render_template
from models.producto import Producto

cliente_routes = Blueprint('cliente_routes', __name__)

@cliente_routes.route('/cliente')
def panel_cliente():
    productos = Producto.query.all()
    # usuario = ... (si lo necesitas)
    return render_template('cliente.html', productos=productos, usuario=usuario)