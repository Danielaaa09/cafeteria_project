# models/mesa.py
from app import db

class Mesa(db.Model):
    __tablename__ = "mesas"

    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.Integer, unique=True, nullable=False)
    estado = db.Column(db.String(20), default="disponible")  # disponible, ocupada

    ordenes = db.relationship("Orden", backref="mesa", lazy=True)
