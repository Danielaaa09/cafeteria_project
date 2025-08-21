# Ejemplo en tu routes/menu_routes.py
from flask import Blueprint, render_template
from models.producto import Producto

menu_routes = Blueprint('menu_routes', __name__)

@menu_routes.route('/menu')
def menu():
    productos = Producto.query.all()
    return render_template('menu.html', productos=productos)