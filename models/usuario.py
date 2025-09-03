from werkzeug.security import generate_password_hash, check_password_hash
from app import db
import datetime

class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    telefono = db.Column(db.String(100))
    direccion = db.Column(db.String(100))
    contrasena_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.Enum('cliente', 'empleado', 'administrador', name='rol_enum'), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    debe_cambiar_contrasena = db.Column(db.Boolean, default=False)

    def set_password(self, contrasena):
        self.contrasena_hash = generate_password_hash(contrasena)

    def check_password(self, contrasena):
        return check_password_hash(self.contrasena_hash, contrasena)
