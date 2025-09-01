from flask import Blueprint, render_template
import json

empleados_routes = Blueprint("empleados_routes", __name__)

@empleados_routes.route("/empleado")
def panel_empleado():
    # 🔹 Aquí en el futuro puedes traer las mesas desde la BD:
    # mesas = Mesa.query.all()
    # mesas = [{"id": m.id, "estado": m.estado} for m in mesas]

    # 🔹 De momento dejamos algunas mesas de ejemplo:
    mesas = [
        {"id": 1, "estado": "Disponible"},
        {"id": 2, "estado": "Ocupada"},
        {"id": 3, "estado": "Disponible"},
        {"id": 4, "estado": "Ocupada"},
    ]

    mesas_json = json.dumps(mesas)

    # 🔹 Simulamos un usuario logueado (cuando conectes auth, pon el real)
    usuario = {"nombre_completo": "Empleado Demo"}

    return render_template(
        "empleado.html",
        usuario=usuario,
        mesas_json=mesas_json
    )
