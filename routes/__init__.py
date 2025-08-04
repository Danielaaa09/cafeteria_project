from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    db.init_app(app)

    from app.routes import Departments_routes, Employees_routes, DepartametsEmployes_routes
    app.register_blueprint(Departments_routes.bp)
    app.register_blueprint(Employees_routes.bp)
    app.register_blueprint(DepartametsEmployes_routes.bp)


    return app