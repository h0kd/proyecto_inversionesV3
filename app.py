from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_login import LoginManager, login_required, logout_user, login_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from database import get_db_connection
from models import User
import pandas as pd
import plotly.express as px
import plotly.io as pio
import os

# Blueprints
from blueprints.acciones import acciones_bp
from blueprints.fondos_mutuos import fondos_mutuos_bp
from blueprints.facturas import facturas_bp
from blueprints.deposito_a_plazo import deposito_a_plazo_bp
from blueprints.boletas_garantia import boletas_garantia_bp
from blueprints.polizas import polizas_bp
from blueprints.bancos import bancos_bp
from blueprints.empresas import empresas_bp
from blueprints.corredores import corredores_bp
from blueprints.companias import companias_bp
from blueprints.clientes import clientes_bp
from blueprints.parametros import parametros_bp
from blueprints.dividendos import dividendos_bp

# Cargar variables de entorno
load_dotenv()

# Configuración de Flask
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Ruta de inicio de sesión

# Registrar el Blueprint
app.register_blueprint(acciones_bp)
app.register_blueprint(fondos_mutuos_bp)
app.register_blueprint(facturas_bp)
app.register_blueprint(deposito_a_plazo_bp)
app.register_blueprint(boletas_garantia_bp)
app.register_blueprint(polizas_bp)
app.register_blueprint(bancos_bp)
app.register_blueprint(empresas_bp)
app.register_blueprint(corredores_bp)
app.register_blueprint(companias_bp)
app.register_blueprint(clientes_bp)
app.register_blueprint(parametros_bp)
app.register_blueprint(dividendos_bp)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # Directorio base de la aplicación
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')  # Ruta absoluta
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Crea la carpeta si no existe

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, NombreUsuario, Contraseña FROM Usuarios WHERE NombreUsuario = %s", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()

        if user_data:
            user_id, db_username, db_password = user_data
            if check_password_hash(db_password, password):
                user = User(id=user_id, username=db_username)
                login_user(user)
                flash('Inicio de sesión exitoso', 'success')
                return redirect(url_for('index'))
            else:
                flash('Contraseña incorrecta', 'danger')
        else:
            flash('Usuario no encontrado', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Cierre de sesión exitoso', 'success')
    return redirect(url_for('login'))

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    query = """
        SELECT ti.Nombre AS TipoInversion, SUM(f.SubTotal) AS Total
        FROM Facturas f
        JOIN TipoInversion ti ON f.ID_TipoInversion = ti.ID
        GROUP BY ti.Nombre
        ORDER BY Total DESC;
    """
    df = pd.read_sql(query, conn)
    conn.close()

    fig = px.bar(df, x='tipoinversion', y='total', title='Total por Tipo de Inversión')
    graph_html = pio.to_html(fig, full_html=False)

    return render_template('index.html', graph=graph_html)

# desde aca debo cambiar todo de lugar

@app.route('/cambiar_contrasena', methods=['GET', 'POST'])
@login_required
def cambiar_contrasena():
    if 'user_id' not in session:
        flash("Debe iniciar sesión para cambiar la contraseña.", "error")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        try:
            contrasena_actual = request.form['contrasena_actual']
            nueva_contrasena = request.form['nueva_contrasena']
            confirmar_contrasena = request.form['confirmar_contrasena']

            # Verificar la contraseña actual
            cursor.execute("SELECT Contraseña FROM Usuarios WHERE ID = %s", (session['user_id'],))
            resultado = cursor.fetchone()

            if not resultado:
                flash("Usuario no encontrado.", "error")
                return redirect(url_for('cambiar_contrasena'))

            contrasena_hash = resultado[0]
            if not check_password_hash(contrasena_hash, contrasena_actual):
                flash("La contraseña actual es incorrecta.", "error")
                return redirect(url_for('cambiar_contrasena'))

            if nueva_contrasena != confirmar_contrasena:
                flash("Las nuevas contraseñas no coinciden.", "error")
                return redirect(url_for('cambiar_contrasena'))

            # Actualizar la nueva contraseña
            nuevo_hash = generate_password_hash(nueva_contrasena)
            cursor.execute("UPDATE Usuarios SET Contraseña = %s WHERE ID = %s", (nuevo_hash, session['user_id']))
            conn.commit()

            flash("Contraseña cambiada con éxito.", "success")
            return redirect(url_for('inicio'))
        except Exception as e:
            print(f"Error al cambiar la contraseña: {e}")
            flash("Hubo un error al cambiar la contraseña.", "error")
            return redirect(url_for('cambiar_contrasena'))
        finally:
            cursor.close()
            conn.close()

    return render_template('cambiar_contrasena.html')

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run(debug=True)