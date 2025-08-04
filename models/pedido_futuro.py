from app import db

class PedidoFuturo(db.Model):
    __tablename__ = 'pedidos_futuros'
    id = db.Column(db.Integer, primary_key=True)
    cantidad_pedida = db.Column(db.Integer, nullable=False)
    fecha_pedido = db.Column(db.Date, nullable=False)
    fecha_llegada = db.Column(db.Date, nullable=False)
    precio_total = db.Column(db.Float, nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'))
