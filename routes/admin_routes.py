
from flask import Blueprint, request, jsonify, render_template
from models.usuario import Usuario
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from models.categoria import Categoria

admin_routes = Blueprint('admin_routes', __name__)

def enviar_correo(destinatario, contrasena_temporal, nombre_completo=None):
    remitente = 'cafeterialasdosamigas@gmail.com'
    password = 'doehmsrgujcalrrj'

    mensaje = MIMEMultipart()
    mensaje['From'] = remitente
    mensaje['To'] = destinatario
    mensaje['Subject'] = 'Tu nueva contraseña temporal'

    if nombre_completo:
        saludo = f"¡Bienvenido {nombre_completo}!"
    else:
        saludo = "¡Bienvenido!"

    cuerpo = f"""
{saludo}

Tu nueva contraseña temporal es: {contrasena_temporal}

Por favor cámbiala después de iniciar sesión.
"""

    mensaje.attach(MIMEText(cuerpo, 'plain', 'utf-8'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(remitente, password)
            server.sendmail(remitente, destinatario, mensaje.as_string())
        print("Correo enviado correctamente.")
    except Exception as e:
        print(f"Error al enviar correo: {e}")

@admin_routes.route('/anadir_producto', methods=['GET', 'POST'])
def anadir_producto():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        precio = float(request.form.get('precio'))
        es_rotativo = bool(int(request.form.get('es_rotativo')))
        categorias_id_raw = request.form.get('categorias_id')
        mensaje = None
        if not categorias_id_raw:
            mensaje = 'Debes seleccionar una categoría.'
        else:
            try:
                categorias_id = int(categorias_id_raw)
                from models.producto import Producto
                from app import db
                nuevo_producto = Producto(
                    nombre=nombre,
                    descripcion=descripcion,
                    precio=precio,
                    es_rotativo=es_rotativo,
                    categorias_id=categorias_id
                )
                db.session.add(nuevo_producto)
                db.session.commit()
                mensaje = 'Producto agregado correctamente.'
            except Exception as e:
                mensaje = f'Error al agregar producto: {str(e)}'
    else:
        mensaje = None
    categorias = Categoria.query.all()
    return render_template('admin/anadir_producto.html', categorias=categorias, mensaje=mensaje)

@admin_routes.route('/dashboard', methods=['GET'])
def dashboard():
    usuarios = Usuario.query.all()
    return render_template('admin/dashboard.html', usuarios=usuarios)

@admin_routes.route('/add_empleado', methods=['GET', 'POST'])
def add_empleado():
    if request.method == 'POST':
        nombre = request.form.get('nombre_completo')
        correo = request.form.get('correo')
        telefono = request.form.get('telefono')
        contrasena_temporal = 'abc123Ñ'  

        nuevo_empleado = Usuario(
            nombre_completo=nombre,
            correo=correo,
            telefono=telefono,
            rol='empleado',
            debe_cambiar_contrasena=True
        )
        nuevo_empleado.set_password(contrasena_temporal)
        from app import db
        db.session.add(nuevo_empleado)
        db.session.commit()

        enviar_correo(correo, contrasena_temporal, nombre_completo=nombre)
        return render_template('admin/anadir_empleado.html', mensaje='Empleado agregado y correo enviado.')
    return render_template('admin/anadir_empleado.html')
