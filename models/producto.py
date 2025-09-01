from app import db

class Producto(db.Model):
    __tablename__ = "producto"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(255), nullable=True)
    precio = db.Column(db.Float, nullable=False)
    es_rotativo = db.Column(db.Boolean, default=False)
    categorias_id = db.Column(db.Integer, db.ForeignKey("categorias.id"), nullable=False)
    imagen_url = db.Column(db.String(255), nullable=True)
    cantidad = db.Column(db.Integer, nullable=False, default=0)

    # relación con DetalleVenta
    detalle_ventas = db.relationship("DetalleVenta", back_populates="producto", lazy=True)
