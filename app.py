from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask import render_template

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost:3306/cafeteria'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'tu_clave_secreta_aqui'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

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

@app.route('/login')
def login():
    return render_template('login.html')
