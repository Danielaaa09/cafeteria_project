from app import db
from datetime import datetime

class HistorialInventario(db.Model):
    __tablename__ = 'historial_inventario'
    id = db.Column(db.Integer, primary_key=True)
    fecha_movimiento = db.Column(db.DateTime, default=datetime.utcnow)
    tipo_movimiento = db.Column(db.Enum('entrada', 'salida', name='tipo_movimiento_enum'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    descripcion = db.Column(db.String(255))
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'))
