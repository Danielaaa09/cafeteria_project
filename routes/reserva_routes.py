# Ejemplo en tu routes/reserva_routes.py
from flask import Blueprint, render_template

reserva_routes = Blueprint('reserva_routes', __name__)

@reserva_routes.route('/reserva')
def reserva():
    return render_template('reserva.html')