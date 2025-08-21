from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from models.usuario import Usuario
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from models.categoria import Categoria
import os
from werkzeug.utils import secure_filename

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
        imagen = request.files.get('imagen')
        imagen_url = None
        if imagen and imagen.filename != '':
            filename = secure_filename(imagen.filename)
            carpeta_destino = os.path.join('static', 'img')
            os.makedirs(carpeta_destino, exist_ok=True)
            ruta = os.path.join(carpeta_destino, filename)
            imagen.save(ruta)
            imagen_url = f'/static/img/{filename}'
        if not categorias_id_raw:
            flash('Debes seleccionar una categoría.', 'error')
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
                    categorias_id=categorias_id,
                    imagen_url=imagen_url  # Asegúrate de tener este campo en tu modelo
                )
                db.session.add(nuevo_producto)
                db.session.commit()
                flash('Producto agregado correctamente.', 'success')
            except Exception as e:
                flash(f'Error al agregar producto: {str(e)}', 'error')
        return redirect(url_for('admin_routes.dashboard'))
    return redirect(url_for('admin_routes.dashboard'))

@admin_routes.route('/dashboard', methods=['GET'])
def dashboard():
    usuarios = Usuario.query.all()
    categorias = Categoria.query.all()  # <-- Agrega esta línea
    return render_template('admin/dashboard.html', usuarios=usuarios, categorias=categorias)  # <-- Y pásala aquí

@admin_routes.route('/add_empleado', methods=['GET', 'POST'])
def add_empleado():
    if request.method == 'POST':
        nombre = request.form.get('nombre_completo')
        correo = request.form.get('correo')
        contrasena_temporal = 'abc123Ñ'  

        nuevo_empleado = Usuario(
            nombre_completo=nombre,
            correo=correo,
            rol='empleado',
            debe_cambiar_contrasena=True
        )
        nuevo_empleado.set_password(contrasena_temporal)
        from app import db
        db.session.add(nuevo_empleado)
        db.session.commit()

        enviar_correo(correo, contrasena_temporal, nombre_completo=nombre)
        flash('Empleado agregado y correo enviado.', 'success')
        return redirect(url_for('admin_routes.dashboard'))
    return redirect(url_for('admin_routes.dashboard'))






