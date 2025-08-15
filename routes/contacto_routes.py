# Ejemplo en tu routes/menu_routes.py
from flask import Blueprint, render_template

contacto_routes = Blueprint('contacto_routes', __name__)

@contacto_routes.route('/contacto')
def contacto():
    return render_template('contacto.html')
