from app import db
from datetime import datetime

class Venta(db.Model):
    __tablename__ = "ventas"

    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    usuarios_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    metodo_pago = db.Column(db.String(50), nullable=False)
    total = db.Column(db.Float, nullable=False)

    # relación con DetalleVenta
    detalles = db.relationship("DetalleVenta", back_populates="venta", lazy=True)
