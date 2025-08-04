from app import db

class Producto(db.Model):
    __tablename__ = 'producto'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(100))
    precio = db.Column(db.Float, nullable=False)
    es_rotativo = db.Column(db.Boolean, nullable=False)
    categorias_id = db.Column(db.Integer, db.ForeignKey('categorias.id'))

    inventario = db.relationship('Inventario', backref='producto', uselist=False)
    historial = db.relationship('HistorialInventario', backref='producto', lazy=True)
    detalle_ventas = db.relationship('DetalleVenta', backref='producto', lazy=True)
    pedidos_futuros = db.relationship('PedidoFuturo', backref='producto', lazy=True)
