from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from config import settings

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.constructed_database_url
    app.config['SECRET_KEY'] = settings.SECRET_KEY

    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    from models.usuario import Usuario
    from models.categoria import Categoria
    from models.producto import Producto
    from models.inventario import Inventario
    from models.venta import Venta
    from models.detalle_venta import DetalleVenta
    from models.historial_inventario import HistorialInventario
    from models.pedido_futuro import PedidoFuturo

    from routes.usuarios_route import usuarios_bp
    from routes.productos_route import productos_bp
    from routes.inventario_route import inventario_bp
    from routes.ventas_route import ventas_bp
    from routes.historial_route import historial_bp
    from routes.pedidos_route import pedidos_bp
    from routes.auth_routes import auth_routes  
    from routes.admin_routes import admin_routes

    app.register_blueprint(usuarios_bp, url_prefix='/api')
    app.register_blueprint(productos_bp, url_prefix='/api')
    app.register_blueprint(inventario_bp, url_prefix='/api')
    app.register_blueprint(ventas_bp, url_prefix='/api')
    app.register_blueprint(historial_bp, url_prefix='/api')
    app.register_blueprint(pedidos_bp, url_prefix='/api')
    app.register_blueprint(auth_routes)
    app.register_blueprint(admin_routes, url_prefix='/admin')

    @app.route('/')
    def index():
        return render_template('paginaprin.html')

    return app
