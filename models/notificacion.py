from app import db
from datetime import datetime

class Notificacion(db.Model):
    __tablename__ = 'notificaciones'
    id = db.Column(db.Integer, primary_key=True)
    mensaje = db.Column(db.String(255), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    tipo = db.Column(db.String(50), default='pedido')
    datos = db.Column(db.Text)  # Aquí puedes guardar los datos del pedido en JSON
