from app import db
from datetime import datetime

class Venta(db.Model):
    __tablename__ = 'ventas'
    id = db.Column(db.Integer, primary_key=True)
    fecha_venta = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)
    usuarios_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))

    detalles = db.relationship('DetalleVenta', backref='venta', lazy=True)
   