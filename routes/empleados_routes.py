from flask import Blueprint, render_template, request, jsonify, session
from app import db
from models.producto import Producto
from models.mesa import Mesa
from models.orden import Orden
from models.detalle_orden import DetalleOrden

empleados_routes = Blueprint("empleados_routes", __name__)

# Panel principal del mesero
@empleados_routes.route("/empleado")
def empleado_panel():
    mesas = Mesa.query.all()
    mesas_json = [{"id": m.id, "numero": m.numero, "estado": m.estado} for m in mesas]

    productos = Producto.query.all()
    productos_json = [
        {"id": p.id, "nombre": p.nombre, "precio": float(p.precio), "categoria": p.categoria}
        for p in productos
    ]

    ordenes = Orden.query.filter_by(estado="pendiente").all()
    ordenes_json = [
        {"id": o.id, "mesa_id": o.mesa_id, "total": float(o.total), "estado": o.estado}
        for o in ordenes
    ]

    return render_template(
        "empleado.html",
        mesas_json=mesas_json,
        productos_json=productos_json,
        ordenes_json=ordenes_json
    )


# Crear una nueva orden
@empleados_routes.route("/empleado/orden/nueva", methods=["POST"])
def nueva_orden():
    data = request.get_json()
    mesa_id = data.get("mesa_id")
    productos = data.get("productos", [])

    mesa = Mesa.query.get(mesa_id)
    if not mesa:
        return jsonify({"success": False, "error": "Mesa no encontrada"}), 404

    mesa.estado = "ocupada"
    orden = Orden(mesa_id=mesa_id, estado="pendiente", total=0)
    db.session.add(orden)
    db.session.flush()  # obtener ID antes de commit

    total = 0
    for item in productos:
        producto = Producto.query.get(item["id"])
        if not producto:
            continue
        cantidad = item.get("cantidad", 1)
        subtotal = producto.precio * cantidad
        total += subtotal

        detalle = DetalleOrden(
            orden_id=orden.id,
            producto_id=producto.id,
            cantidad=cantidad,
            subtotal=subtotal
        )
        db.session.add(detalle)

    orden.total = total
    db.session.commit()

    return jsonify({"success": True, "orden_id": orden.id, "total": total})


# Agregar productos a orden existente
@empleados_routes.route("/empleado/orden/<int:orden_id>/agregar", methods=["POST"])
def agregar_a_orden(orden_id):
    data = request.get_json()
    productos = data.get("productos", [])

    orden = Orden.query.get(orden_id)
    if not orden or orden.estado != "pendiente":
        return jsonify({"success": False, "error": "Orden no válida"}), 400

    total = orden.total
    for item in productos:
        producto = Producto.query.get(item["id"])
        if not producto:
            continue
        cantidad = item.get("cantidad", 1)
        subtotal = producto.precio * cantidad
        total += subtotal

        detalle = DetalleOrden(
            orden_id=orden.id,
            producto_id=producto.id,
            cantidad=cantidad,
            subtotal=subtotal
        )
        db.session.add(detalle)

    orden.total = total
    db.session.commit()

    return jsonify({"success": True, "nuevo_total": total})


# Finalizar orden (pagar)
@empleados_routes.route("/empleado/orden/<int:orden_id>/pagar", methods=["POST"])
def pagar_orden(orden_id):
    data = request.get_json()
    metodo_pago = data.get("metodo_pago")

    orden = Orden.query.get(orden_id)
    if not orden or orden.estado != "pendiente":
        return jsonify({"success": False, "error": "Orden no válida"}), 400

    orden.estado = "pagada"
    orden.metodo_pago = metodo_pago

    mesa = Mesa.query.get(orden.mesa_id)
    mesa.estado = "disponible"

    db.session.commit()
    return jsonify({"success": True, "mensaje": "Orden pagada con éxito"})
