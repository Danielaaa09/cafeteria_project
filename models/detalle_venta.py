from app import db

class DetalleVenta(db.Model):
    __tablename__ = "detalle_ventas"

    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey("ventas.id"), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("producto.id"), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

    # relaciones inversas
    venta = db.relationship("Venta", back_populates="detalles")
    producto = db.relationship("Producto", back_populates="detalle_ventas")
