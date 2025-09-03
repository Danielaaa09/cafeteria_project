# models/orden.py
from app import db
import datetime

class Orden(db.Model):
    __tablename__ = "ordenes"

    id = db.Column(db.Integer, primary_key=True)
    mesa_id = db.Column(db.Integer, db.ForeignKey("mesas.id"), nullable=False)
    estado = db.Column(db.String(20), default="pendiente")  
    # pendiente, en_preparacion, servido, pagado

    metodo_pago = db.Column(db.String(20), nullable=True)  
    total = db.Column(db.Float, default=0.0)
    fecha_creacion = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    detalles = db.relationship("DetalleOrden", backref="orden", lazy=True)
