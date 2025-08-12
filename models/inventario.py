from app import db
from datetime import datetime

class Inventario(db.Model):
    __tablename__ = 'inventario'
    id = db.Column(db.Integer, primary_key=True)
    cantidad_disponible = db.Column(db.Integer, nullable=False)
    cantidad_minima = db.Column(db.Integer, nullable=False)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    rotativo = db.Column(db.Enum('si', 'no', name = 'rotativo_enum'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'))
