# Ejemplo en tu routes/menu_routes.py
from flask import Blueprint, render_template

menu_routes = Blueprint('menu_routes', __name__)

@menu_routes.route('/menu')
def menu():
    return render_template('menu.html')