# Ejemplo en tu routes/acerca_routes.py
from flask import Blueprint, render_template

acerca_routes = Blueprint('acerca_routes', __name__)

@acerca_routes.route('/acerca')
def acerca():
    return render_template('acercade.html')