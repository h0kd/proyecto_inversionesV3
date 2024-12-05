from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_login import LoginManager, login_required, logout_user, login_user
import pandas as pd
import plotly.express as px
import plotly.io as pio
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from blueprints.acciones import acciones_bp
from database import get_db_connection
from models import User

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

# Configuración básica
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

@app.route('/add_factura', methods=['GET', 'POST'])
@login_required
def add_factura():
    if request.method == 'POST':
        # Recibir datos del formulario
        numero_factura = request.form['numero_factura']
        rut_entidad = request.form['rut_entidad']

        # Validar que solo contengan números
        if not numero_factura.isdigit():
            return "Error: El número de factura debe contener solo dígitos.", 400
        if not rut_entidad.isdigit():
            return "Error: El RUT de la entidad debe contener solo dígitos.", 400

        # Continuar con el resto de la lógica
        nombre_entidad = request.form['nombre_entidad'].upper()
        tipo_entidad = request.form['tipo_entidad']
        fecha = request.form['fecha']
        tipo = request.form['tipo'].capitalize()
        cantidad = float(request.form['cantidad'])
        precio_unitario = float(request.form['precio_unitario'])
        subtotal = float(request.form['subtotal'])
        valor_total = float(request.form['valor_total'])
        nombre_activo = request.form['nombre_activo'].upper()
        comision = request.form.get('comision')
        gasto = request.form.get('gasto')


        # Manejar archivo adjunto
        if 'archivo_factura' not in request.files:
            return "Error: No se adjuntó un archivo.", 400

        archivo = request.files['archivo_factura']
        if archivo.filename == '':
            return "Error: No se seleccionó un archivo.", 400

        if archivo and allowed_file(archivo.filename):
            filename = secure_filename(archivo.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file_path = file_path.replace("\\", "/")  # Convertir barras invertidas a barras normales
            archivo.save(file_path)  # Guardar el archivo
        else:
            return "Error: El archivo no es válido. Solo se aceptan PDFs.", 400

        # Determinar el ID de Tipo de Inversión según el tipo
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ID FROM TipoInversion WHERE Nombre = %s", (tipo,))
        tipo_inversion_result = cursor.fetchone()
        if not tipo_inversion_result:
            cursor.close()
            conn.close()
            return "Error: Tipo de Inversión no encontrado.", 400
        id_tipo_inversion = tipo_inversion_result[0]

        # Verificar si la Entidad ya existe en la base de datos
        cursor.execute("SELECT ID_Entidad FROM Entidad WHERE Rut = %s", (rut_entidad,))
        entidad_result = cursor.fetchone()
        if not entidad_result:
            # Si la entidad no existe, crearla
            cursor.execute("""
                INSERT INTO Entidad (Rut, Nombre, TipoEntidad)
                VALUES (%s, %s, %s);
            """, (rut_entidad, nombre_entidad, tipo_entidad))
            conn.commit()
            cursor.execute("SELECT ID_Entidad FROM Entidad WHERE Rut = %s", (rut_entidad,))
            entidad_result = cursor.fetchone()

        id_corredora = entidad_result[0]  # Extraer la ID de la Entidad

        # Insertar la factura en la base de datos
        cursor.execute("""
            INSERT INTO Facturas 
            (NumeroFactura, ID_Corredora, Rut, Fecha, Tipo, Cantidad, PrecioUnitario, SubTotal, Valor, NombreActivo, Comision, Gasto, ID_TipoInversion, AdjuntoFactura)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (numero_factura, id_corredora, rut_entidad, fecha, tipo, cantidad, precio_unitario, subtotal, valor_total, nombre_activo, comision, gasto, id_tipo_inversion, file_path))
        conn.commit()
        cursor.close()
        conn.close()

        # Redirigir después de insertar
        return redirect(url_for('index'))
    else:
        return render_template('facturas/add_factura.html')

@app.route('/listado_facturas', methods=['GET'])
@login_required
def listado_facturas():
    # Obtener los parámetros de ordenación
    sort_by = request.args.get('sort_by', 'NumeroFactura')  # Ordenar por NumeroFactura por defecto
    order = request.args.get('order', 'asc')  # Orden ascendente por defecto

    # Validar las columnas permitidas para ordenar
    valid_columns = ['NumeroFactura', 'NombreEntidad', 'NombreActivo', 'Tipo', 'Fecha', 'Cantidad', 'PrecioUnitario', 'SubTotal', 'Valor']
    if sort_by not in valid_columns:
        sort_by = 'NumeroFactura'  # Valor por defecto si la columna no es válida

    # Validar la dirección del orden
    if order not in ['asc', 'desc']:
        order = 'asc'

    # Conexión a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()

    # Consulta principal para las facturas con orden dinámico
    query = f"""
        SELECT 
            f.NumeroFactura, 
            e.Nombre AS NombreEntidad, 
            f.NombreActivo, 
            f.Tipo,
            f.Fecha, 
            f.Cantidad, 
            f.PrecioUnitario, 
            f.SubTotal, 
            f.Valor, 
            f.AdjuntoFactura
        FROM Facturas f
        JOIN Entidad e ON f.ID_Corredora = e.ID_Entidad
        ORDER BY {sort_by} {order}
    """
    cursor.execute(query)
    facturas = cursor.fetchall()

    return render_template('facturas/listado_facturas.html', facturas=facturas, sort_by=sort_by, order=order)

@app.route('/edit_factura/<int:numero_factura>', methods=['GET', 'POST'])
@login_required
def editar_factura(numero_factura):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'POST':
            try:
                # Obtener datos del formulario
                print("Datos recibidos del formulario:", request.form)  # Debug
                nuevo_numero_factura = request.form['nuevo_numero']
                nombre_entidad = request.form['nombre_entidad']
                nombre_activo = request.form['nombre_activo']
                tipo = request.form['tipo']
                fecha = request.form['fecha']
                cantidad = request.form['cantidad']
                comision = request.form['comision']
                gasto = request.form['gasto']

                # Validar si el nuevo número de factura ya existe
                if str(numero_factura) != nuevo_numero_factura:
                    cursor.execute("SELECT 1 FROM Facturas WHERE NumeroFactura = %s", (nuevo_numero_factura,))
                    if cursor.fetchone():
                        flash("El nuevo número de factura ya existe. Por favor, elige otro.", "error")
                        return redirect(url_for('editar_factura', numero_factura=numero_factura))

                # Actualizar entidad o entidad comercial
                cursor.execute("SELECT ID_Corredora FROM Facturas WHERE NumeroFactura = %s", (numero_factura,))
                id_entidad = cursor.fetchone()[0]

                cursor.execute("""
                    UPDATE Entidad
                    SET Nombre = %s
                    WHERE ID_Entidad = %s
                """, (nombre_entidad, id_entidad))

                # Actualizar la factura (incluyendo Nombre Activo)
                cursor.execute("""
                    UPDATE Facturas
                    SET NumeroFactura = %s, NombreActivo = %s, Tipo = %s, Fecha = %s, Cantidad = %s, Comision = %s, Gasto = %s
                    WHERE NumeroFactura = %s
                """, (nuevo_numero_factura, nombre_activo, tipo, fecha, cantidad, comision, gasto, numero_factura))

                if cursor.rowcount == 0:
                    flash("No se pudo actualizar la factura. Verifica los datos.", "error")
                    conn.rollback()
                    return redirect(url_for('editar_factura', numero_factura=numero_factura))

                conn.commit()
                flash("Factura actualizada exitosamente.", "success")
                return redirect(url_for('listado_facturas'))
            except Exception as e:
                conn.rollback()
                flash(f"Error al actualizar la factura: {e}", "error")
        else:
            # Obtener información de la factura
            cursor.execute("SELECT NumeroFactura, NombreActivo, Tipo, Fecha, Cantidad, Comision, Gasto FROM Facturas WHERE NumeroFactura = %s", (numero_factura,))
            factura = cursor.fetchone()

            cursor.execute("""
                SELECT e.Rut, e.Nombre, e.TipoEntidad
                FROM Facturas f
                JOIN Entidad e ON f.ID_Corredora = e.ID_Entidad
                WHERE f.NumeroFactura = %s
            """, (numero_factura,))
            entidad = cursor.fetchone()

            if not entidad:
                cursor.execute("""
                    SELECT ec.Rut, ec.Nombre, ec.TipoEntidad
                    FROM Facturas f
                    JOIN EntidadComercial ec ON f.ID_Corredora = ec.ID_Entidad
                    WHERE f.NumeroFactura = %s
                """, (numero_factura,))
                entidad = cursor.fetchone()

            return render_template('facturas/edit_factura.html', factura=factura, entidad=entidad)

    finally:
        # Asegurar el cierre de conexión
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/eliminar_factura/<int:numero_factura>', methods=['POST', 'GET'])
@login_required
def eliminar_factura(numero_factura):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Eliminar la factura
    cursor.execute("DELETE FROM Facturas WHERE NumeroFactura = %s", (numero_factura,))
    conn.commit()
    conn.close()

    return redirect(url_for('listado_facturas'))

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

@app.route('/test_password', methods=['GET'])
def test_password():
    contraseña_original = 'admin123'
    contraseña_hash = generate_password_hash(contraseña_original)

    # Probar verificación
    resultado = check_password_hash(contraseña_hash, contraseña_original)
    return f"Hash generado: {contraseña_hash}, Verificación: {resultado}"

@app.route('/deposito_a_plazo', methods=['GET'])
@login_required
def deposito_a_plazo():
    # Obtener los parámetros de ordenación
    sort_by = request.args.get('sort_by', 'ID_Deposito')  # Ordenar por ID_Deposito por defecto
    order = request.args.get('order', 'asc')  # Orden ascendente por defecto

    # Validar las columnas permitidas para ordenar
    valid_columns = [
        'ID_Deposito', 'Empresa', 'Banco', 'FechaEmision', 'FechaVencimiento', 'Moneda',
        'MontoInicial', 'MontoFinal', 'TipoDeposito', 'CapitalRenovacion', 'PlazoRenovacion'
    ]
    if sort_by not in valid_columns:
        sort_by = 'ID_Deposito'  # Valor por defecto si la columna no es válida

    # Validar la dirección del orden
    if order not in ['asc', 'desc']:
        order = 'asc'

    # Conexión a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()

    # Consulta SQL
    query = f"""
        SELECT 
            d.ID_Deposito,
            ec.Nombre AS Empresa,
            b.Nombre AS Banco,
            d.FechaEmision,
            d.FechaVencimiento,
            d.Moneda,
            d.MontoInicial,
            d.MontoFinal,
            d.TipoDeposito,
            d.CapitalRenovacion,
            d.PlazoRenovacion,
            d.Comprobante
        FROM DepositoAPlazo d
        JOIN EntidadComercial ec ON d.ID_EntidadComercial = ec.ID_Entidad
        JOIN Entidad b ON d.ID_Banco = b.ID_Entidad
        ORDER BY {sort_by} {order}
    """
    cursor.execute(query)
    depositos = cursor.fetchall()

    cursor.close()
    conn.close()

    # Renderizar la plantilla con los datos recuperados
    return render_template('depositos/deposito_a_plazo.html', depositos=depositos, sort_by=sort_by, order=order)

from datetime import datetime

@app.route('/add_deposito', methods=['GET', 'POST'])
@login_required
def add_deposito():
    if request.method == 'POST':
        # Conexión a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Capturar datos del formulario
            id_deposito = request.form['numero_deposito']  # Número de Depósito
            tipo = request.form['tipo']
            monto = float(request.form['monto'])
            fecha_emision = request.form['fecha_emision']
            tasa_interes = float(request.form['tasa_interes'])
            fecha_vencimiento = request.form['fecha_vencimiento']
            moneda = request.form.get('moneda', 'CLP')
            interes_ganado = float(request.form.get('interes_ganado', 0))  # Valor opcional con default 0
            tipo_beneficiario = request.form['tipo_beneficiario']  # Cliente o Empresa
            nombre_beneficiario = request.form.get('nombre_beneficiario', '').upper()
            rut_beneficiario = request.form.get('rut_beneficiario', '')

            # Manejo de errores
            if not nombre_beneficiario:
                return "Error: Nombre del beneficiario no proporcionado", 400

            # Validar campos de renovación (solo si tipo es "Renovable")
            capital_renovacion = float(request.form.get('capital_renovacion', 0))
            fecha_emision_renovacion = request.form.get('fecha_emision_renovacion')
            tasa_interes_renovacion = float(request.form.get('tasa_interes_renovacion', 0))
            plazo_renovacion = int(request.form.get('plazo_renovacion', 0))
            tasa_periodo = float(request.form.get('tasa_periodo', 0))
            fecha_vencimiento_renovacion = request.form.get('fecha_vencimiento_renovacion')
            total_pagar_renovacion = float(request.form.get('total_pagar_renovacion', 0))

            # Manejo del archivo comprobante
            comprobante = None
            if 'comprobante' in request.files:
                file = request.files['comprobante']
                if file and file.filename != '':
                    filename = secure_filename(file.filename)
                    comprobante_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(comprobante_path)
                    comprobante = comprobante_path.replace("\\", "/")

            # Manejo del beneficiario
            cursor.execute(
                "SELECT ID_Entidad FROM EntidadComercial WHERE Rut = %s AND TipoEntidad = %s",
                (rut_beneficiario, tipo_beneficiario)
            )
            entidad_result = cursor.fetchone()

            if not entidad_result:
                # Crear beneficiario si no existe
                cursor.execute(
                    """
                    INSERT INTO EntidadComercial (Rut, Nombre, TipoEntidad)
                    VALUES (%s, %s, %s) RETURNING ID_Entidad
                    """,
                    (rut_beneficiario, nombre_beneficiario, tipo_beneficiario)
                )
                id_entidadcomercial = cursor.fetchone()[0]
            else:
                id_entidadcomercial = entidad_result[0]

            # Manejo del banco
            banco_nombre = request.form['banco'].upper()
            cursor.execute("SELECT ID_Entidad FROM Entidad WHERE Nombre = %s", (banco_nombre,))
            banco_result = cursor.fetchone()

            if not banco_result:
                # Crear el banco si no existe
                rut_temporal = f"TEMP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                cursor.execute(
                    """
                    INSERT INTO Entidad (Rut, Nombre, TipoEntidad)
                    VALUES (%s, %s, 'Banco') RETURNING ID_Entidad
                    """,
                    (rut_temporal, banco_nombre)
                )
                id_banco = cursor.fetchone()[0]
            else:
                id_banco = banco_result[0]

            # Insertar el depósito en la base de datos
            cursor.execute("""
                INSERT INTO DepositoAPlazo 
                (ID_Deposito, ID_Banco, ID_EntidadComercial, FechaEmision, FechaVencimiento, Moneda, MontoInicial, TipoDeposito, 
                InteresGanado, TasaInteres, CapitalRenovacion, FechaEmisionRenovacion, TasaInteresRenovacion, 
                PlazoRenovacion, TasaPeriodo, FechaVencimientoRenovacion, TotalPagarRenovacion, Comprobante)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                id_deposito, id_banco, id_entidadcomercial, fecha_emision, fecha_vencimiento, moneda, monto, tipo, 
                interes_ganado, tasa_interes, 
                capital_renovacion if tipo == "Renovable" else None, 
                fecha_emision_renovacion if tipo == "Renovable" else None, 
                tasa_interes_renovacion if tipo == "Renovable" else None, 
                plazo_renovacion if tipo == "Renovable" else None, 
                tasa_periodo if tipo == "Renovable" else None, 
                fecha_vencimiento_renovacion if tipo == "Renovable" else None, 
                total_pagar_renovacion if tipo == "Renovable" else None,
                comprobante
            ))

            conn.commit()

        except Exception as e:
            conn.rollback()
            print(f"Error al insertar el depósito: {e}")
            raise e

        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('depositos/deposito_a_plazo'))

    return render_template('depositos/add_deposito.html')


@app.route('/edit_deposito/<int:id_deposito>', methods=['GET', 'POST'])
@login_required
def edit_deposito(id_deposito):
    # Conexión a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        try:
            # Capturar datos del formulario
            id_deposito_new = request.form['id_deposito']
            tipo = request.form['tipo']
            monto = float(request.form['monto'])
            fecha_emision = request.form['fecha_emision']
            tasa_interes = float(request.form['tasa_interes'])
            fecha_vencimiento = request.form['fecha_vencimiento']
            interes_ganado = float(request.form['interes_ganado'])  
            reajuste_ganado = request.form.get('reajuste_ganado', None)

            print(request.form)
            # Manejo del comprobante
            comprobante = None
            if 'comprobante' in request.files and request.files['comprobante'].filename:
                file = request.files['comprobante']
                if file and allowed_file(file.filename):  # Verifica extensión válida
                    filename = secure_filename(file.filename)
                    comprobante = os.path.join(app.config['UPLOAD_FOLDER'], filename).replace("\\", "/")
                    file.save(comprobante)  # Guarda el archivo en el servidor
            else:
                # Si no se adjunta nuevo comprobante, usar el existente
                cursor.execute("SELECT Comprobante FROM DepositoAPlazo WHERE ID_Deposito = %s", (id_deposito,))
                comprobante = cursor.fetchone()[0]  # Mantén el comprobante actual

            # Construir consulta SQL para actualización
            update_query = """
                UPDATE DepositoAPlazo
                SET ID_Deposito = %s,
                    TipoDeposito = %s,
                    MontoInicial = %s,
                    FechaEmision = %s,
                    FechaVencimiento = %s,
                    InteresGanado = %s,
                    TasaInteres = %s,
                    ReajusteGanado = %s,
                    Comprobante = %s
                WHERE ID_Deposito = %s
            """
            cursor.execute(update_query, (
                id_deposito_new,
                tipo,
                monto,
                fecha_emision,
                fecha_vencimiento,
                interes_ganado,
                tasa_interes,
                reajuste_ganado,
                comprobante,
                id_deposito
            ))

            # Confirmar cambios
            conn.commit()

        except Exception as e:
            conn.rollback()
            print(f"Error al actualizar el depósito: {e}")
            raise e

        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('deposito_a_plazo'))

    # Cargar datos existentes para el formulario
    cursor.execute("SELECT * FROM DepositoAPlazo WHERE ID_Deposito = %s", (id_deposito,))
    deposito = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('depositos/edit_deposito.html', deposito=deposito)

@app.route('/delete_deposito/<int:id_deposito>', methods=['POST'])
@login_required
def delete_deposito(id_deposito):
    # Conexión a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Eliminar el depósito por su ID
        cursor.execute("DELETE FROM DepositoAPlazo WHERE ID_Deposito = %s", (id_deposito,))
        conn.commit()
        flash('Depósito eliminado exitosamente.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error al eliminar el depósito: {e}', 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('deposito_a_plazo'))

@app.route('/dividendos/<int:id_accion>', methods=['GET'])
@login_required
def historial_dividendos(id_accion):
    # Obtener los parámetros de ordenamiento
    sort_by = request.args.get('sort_by', 'FechaCierre')  # Ordenar por FechaCierre por defecto
    order = request.args.get('order', 'asc')  # Orden ascendente por defecto

    # Validar columnas permitidas para evitar SQL injection
    valid_columns = ['ID_Dividendo', 'Nombre', 'FechaCierre', 'FechaPago', 'ValorPorAccion', 'Moneda', 'ValorTotal', 'Rentabilidad']
    if sort_by not in valid_columns:
        sort_by = 'FechaCierre'  # Valor por defecto si la columna no es válida
    if order not in ['asc', 'desc']:
        order = 'asc'

    # Conexión a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()

    # Consulta dinámica con ordenamiento
    query = f"""
        SELECT ID_Dividendo, Nombre, FechaCierre, FechaPago, ValorPorAccion, Moneda, ValorTotal, Rentabilidad
        FROM Dividendos
        WHERE ID_Accion = %s
        ORDER BY {sort_by} {order}
    """
    cursor.execute(query, (id_accion,))
    dividendos = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template(
        'acciones/dividendos/dividendos.html',
        dividendos=dividendos,
        id_accion=id_accion,
        sort_by=sort_by,
        order=order,
    )

from decimal import Decimal

@app.route('/add_dividendo', methods=['POST'])
@login_required
def add_dividendo():
    # Capturar datos del formulario
    nombre = request.form['nombre']
    fecha_cierre = request.form['fecha_cierre']
    fecha_pago = request.form['fecha_pago']
    valor_por_accion = Decimal(request.form['valor_por_accion'])  # Convertir a Decimal
    moneda = request.form['moneda']
    id_accion = request.form['id_accion']
    
    # Obtener cantidad de acciones y precio promedio para calcular el valor total y la rentabilidad
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Obtener la cantidad total de acciones
    cursor.execute("SELECT Cantidad FROM Accion WHERE ID_Accion = %s", (id_accion,))
    cantidad_acciones = cursor.fetchone()
    if not cantidad_acciones:
        cantidad_acciones = Decimal(0)
    else:
        cantidad_acciones = Decimal(cantidad_acciones[0])

    # Calcular valor total
    valor_total = valor_por_accion * cantidad_acciones

    # Obtener el precio promedio de compra
    cursor.execute("""
        SELECT SUM(Cantidad * PrecioUnitario + COALESCE(Comision, 0)) / SUM(Cantidad)
        FROM Facturas
        WHERE Tipo = 'Compra' AND NombreActivo = (
            SELECT Nombre FROM Accion WHERE ID_Accion = %s
        )
    """, (id_accion,))
    precio_promedio = cursor.fetchone()[0]

    if precio_promedio:
        precio_promedio = Decimal(precio_promedio)
        # Calcular rentabilidad
        rentabilidad = (valor_por_accion / precio_promedio) * 100
    else:
        rentabilidad = Decimal(0)  # Si no hay precio promedio, la rentabilidad es 0

    # Guardar en la base de datos
    cursor.execute("""
        INSERT INTO Dividendos (ID_Accion, Nombre, FechaCierre, FechaPago, ValorPorAccion, Moneda, ValorTotal, Rentabilidad)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (id_accion, nombre, fecha_cierre, fecha_pago, float(valor_por_accion), moneda, float(valor_total), float(rentabilidad)))
    conn.commit()
    cursor.close()
    conn.close()

    flash("Dividendo agregado exitosamente.", "success")
    return redirect(url_for('acciones/dividendos/historial_dividendos', id_accion=id_accion))

@app.route('/dividendos/add/<int:id_accion>', methods=['GET'])
@login_required
def formulario_add_dividendo(id_accion):
    """
    Muestra el formulario para agregar un dividendo asociado a una acción específica.
    """
    return render_template('acciones/dividendos/add_dividendo.html', id_accion=id_accion)

@app.route('/delete_dividendo/<int:id_dividendo>', methods=['POST'])
@login_required
def delete_dividendo(id_dividendo):
    """
    Elimina un dividendo de la base de datos.
    """
    id_accion = request.form.get('id_accion')  # Obtener ID de acción desde el formulario

    if not id_accion:
        flash("No se proporcionó un ID de acción válido.", "error")
        return redirect(url_for('acciones'))  # Redirige a acciones en caso de error

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Eliminar el dividendo con el ID especificado
        cursor.execute("DELETE FROM Dividendos WHERE ID_Dividendo = %s", (id_dividendo,))
        conn.commit()

        flash("Dividendo eliminado exitosamente.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al eliminar el dividendo: {e}", "error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('acciones/dividendos/historial_dividendos', id_accion=id_accion))

@app.route('/edit_dividendo/<int:id_dividendo>', methods=['GET', 'POST'])
@login_required
def edit_dividendo(id_dividendo):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'POST':
            print("POST recibido")  # Debug
            nombre = request.form['nombre']
            fecha_cierre = request.form['fecha_cierre']
            fecha_pago = request.form['fecha_pago']
            valor_por_accion = float(request.form['valor_por_accion'])
            moneda = request.form['moneda']
            id_accion = request.form.get('id_accion')

            if not id_accion:
                flash("Error: No se pudo identificar la acción asociada.", "error")
                return redirect(url_for('acciones'))

            print(f"Datos procesados: nombre={nombre}, fecha_cierre={fecha_cierre}, fecha_pago={fecha_pago}, valor_por_accion={valor_por_accion}, moneda={moneda}, id_accion={id_accion}")  # Debug

            # Calcular el nuevo valor total
            cursor.execute(
                "SELECT Cantidad FROM Accion WHERE ID_Accion = %s",
                (id_accion,)
            )
            cantidad_acciones = cursor.fetchone()
            cantidad_acciones = float(cantidad_acciones[0]) if cantidad_acciones else 0.0  # Convertir a float
            valor_total = valor_por_accion * cantidad_acciones  # Ahora ambos son float

            print(f"Cantidad acciones: {cantidad_acciones}, Valor total calculado: {valor_total}")  # Debug


            # Actualizar el dividendo
            cursor.execute("""
                UPDATE Dividendos
                SET Nombre = %s, FechaCierre = %s, FechaPago = %s, ValorPorAccion = %s, Moneda = %s, ValorTotal = %s
                WHERE ID_Dividendo = %s
            """, (nombre, fecha_cierre, fecha_pago, valor_por_accion, moneda, valor_total, id_dividendo))
            print(f"Dividendo actualizado: {cursor.rowcount} filas afectadas.")  # Debug

            conn.commit()
            print(f"Redirigiendo a historial_dividendos con id_accion: {id_accion}")  # Debug
            flash("Dividendo actualizado exitosamente.", "success")
            return redirect(url_for('historial_dividendos', id_accion=id_accion))

        # Obtener los datos actuales del dividendo
        cursor.execute(
            "SELECT Nombre, FechaCierre, FechaPago, ValorPorAccion, Moneda FROM Dividendos WHERE ID_Dividendo = %s",
            (id_dividendo,)
        )
        dividendo = cursor.fetchone()
        cursor.execute("SELECT ID_Accion FROM Dividendos WHERE ID_Dividendo = %s", (id_dividendo,))
        id_accion = cursor.fetchone()[0]

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error capturado: {e}")  # Debug
        flash(f"Error al procesar la solicitud: {e}", "error")
        return redirect(url_for('acciones'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template('acciones/dividendos/edit_dividendo.html', dividendo=dividendo, id_dividendo=id_dividendo, id_accion=id_accion)

@app.route('/fondos_mutuos', methods=['GET'])
@login_required
def fondos_mutuos():
    # Capturar parámetros de ordenamiento y búsqueda
    sort_by = request.args.get('sort_by', 'f.ID_Fondo')  # Ordenar por ID_Fondo por defecto
    order = request.args.get('order', 'asc')  # Orden ascendente por defecto
    search_query = request.args.get('search', '').strip()  # Capturar la búsqueda

    # Validar columnas permitidas para evitar SQL injection
    valid_columns = {
        'ID_Fondo': 'f.ID_Fondo',
        'Nombre': 'f.Nombre',
        'Empresa': 'e.Nombre',
        'Banco': 'b.Nombre',
        'TipoRiesgo': 'f.TipoRiesgo',
        'MontoInvertido': 'f.MontoInvertido',
        'MontoFinal': 'f.MontoFinal',
        'FechaInicio': 'f.FechaInicio',
        'FechaTermino': 'f.FechaTermino',
        'Rentabilidad': 'Rentabilidad'
    }

    sort_column = valid_columns.get(sort_by, 'f.ID_Fondo')
    if order not in ['asc', 'desc']:
        order = 'asc'

    # Conexión y consulta
    conn = get_db_connection()
    cursor = conn.cursor()

    # Consulta base
    query = f"""
    SELECT 
        f.ID_Fondo, 
        f.Nombre, 
        e.Nombre AS Empresa, 
        b.Nombre AS Banco, 
        f.TipoRiesgo, 
        f.MontoInvertido, 
        f.MontoFinal, 
        f.FechaInicio, 
        f.FechaTermino, 
        CASE 
            WHEN f.MontoFinal IS NOT NULL THEN 
                ROUND(((f.MontoFinal - f.MontoInvertido) / f.MontoInvertido) * 100, 2)
            ELSE NULL
        END AS Rentabilidad,
        f.Comprobante
    FROM FondosMutuos f
    JOIN EntidadComercial e ON f.ID_Entidad = e.ID_Entidad
    JOIN Entidad b ON f.ID_Banco = b.ID_Entidad
    """

    # Agregar filtro de búsqueda si se proporciona un término
    if search_query:
        query += " WHERE e.Nombre ILIKE %s"

    # Ordenar por la columna especificada
    query += f" ORDER BY {sort_column} {order};"

    # Ejecutar la consulta
    if search_query:
        cursor.execute(query, (f"%{search_query}%",))
    else:
        cursor.execute(query)

    fondos = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('fondos/fondos_mutuos.html', fondos=fondos, sort_by=sort_by, order=order, search_query=search_query)

@app.route('/add_fondo_mutuo', methods=['GET', 'POST'])
@login_required
def add_fondo_mutuo():
    if request.method == 'POST':
        print(request.form)  # Imprime todos los datos enviados por el formulario
        # Capturar datos del formulario
        nombre_fondo = request.form['nombre_fondo'].upper()
        monto_invertido = float(request.form.get('monto_invertido'))
        monto_final = request.form.get('monto_final')
        if monto_final:
            monto_final = float(monto_final)
        else:
            monto_final = None  # Usar None para valores nulos en SQL
        riesgo = request.form['riesgo']
        fecha_inicio = request.form['fecha_inicio']
        fecha_termino = request.form.get('fecha_termino')
        if not fecha_termino:  # Si está vacío o None
            fecha_termino = None
        empresa_nombre = request.form['empresa'].upper()
        banco_nombre = request.form['banco'].upper()

        # Manejar archivo comprobante
        comprobante = None
        if 'comprobante' in request.files:
            file = request.files['comprobante']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                comprobante = os.path.join(app.config['UPLOAD_FOLDER'], filename).replace("\\", "/")
                file.save(comprobante)

        # Conectar a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()

        # Buscar o crear banco
        cursor.execute("SELECT ID_Entidad FROM Entidad WHERE Nombre = %s", (banco_nombre,))
        banco_result = cursor.fetchone()
        if not banco_result:
            rut_temporal = f"TEMP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            cursor.execute("""
                INSERT INTO Entidad (Rut, Nombre, TipoEntidad)
                VALUES (%s, %s, 'Banco') RETURNING ID_Entidad
            """, (rut_temporal, banco_nombre))
            id_banco = cursor.fetchone()[0]
        else:
            id_banco = banco_result[0]

        # Buscar o crear empresa
        cursor.execute("SELECT ID_Entidad FROM EntidadComercial WHERE Nombre = %s", (empresa_nombre,))
        empresa_result = cursor.fetchone()
        if not empresa_result:
            rut_temporal = f"TEMP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            cursor.execute("""
                INSERT INTO EntidadComercial (Rut, Nombre, TipoEntidad)
                VALUES (%s, %s, 'Empresa') RETURNING ID_Entidad
            """, (rut_temporal, empresa_nombre))
            id_empresa = cursor.fetchone()[0]
        else:
            id_empresa = empresa_result[0]

        # Insertar fondo mutuo
        cursor.execute("""
            INSERT INTO FondosMutuos 
            (Nombre, MontoInvertido, MontoFinal, Rentabilidad, TipoRiesgo, FechaInicio, FechaTermino, ID_Entidad, ID_Banco, Comprobante)
            VALUES (%s, %s, %s, NULL, %s, %s, %s, %s, %s, %s)
        """, (nombre_fondo, monto_invertido, monto_final, riesgo, fecha_inicio, fecha_termino, id_empresa, id_banco, comprobante))
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('fondos_mutuos'))

    return render_template('fondos/add_fondo_mutuo.html')

@app.route('/edit_fondo_mutuo/<int:id_fondo>', methods=['GET', 'POST'])
@login_required
def edit_fondo_mutuo(id_fondo):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Capturar los datos enviados desde el formulario
        monto_final = request.form.get('monto_final')
        fecha_termino = request.form.get('fecha_termino')

        # Validar y convertir los valores
        monto_final = float(monto_final) if monto_final else None
        fecha_termino = fecha_termino if fecha_termino else None

        # Actualizar la tabla FondosMutuos
        cursor.execute("""
            UPDATE FondosMutuos
            SET MontoFinal = %s, FechaTermino = %s
            WHERE ID_Fondo = %s
        """, (monto_final, fecha_termino, id_fondo))

        conn.commit()
        cursor.close()
        conn.close()

        # Redirigir al listado después de guardar
        return redirect(url_for('fondos_mutuos'))

    # Si es GET, obtener los datos del fondo actual para mostrar en el formulario
    cursor.execute("""
        SELECT ID_Fondo, Nombre, MontoFinal, FechaTermino
        FROM FondosMutuos
        WHERE ID_Fondo = %s
    """, (id_fondo,))
    fondo = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('fondos/edit_fondo_mutuo.html', fondo=fondo)

@app.route('/delete_fondo_mutuo/<int:id_fondo>', methods=['POST'])
@login_required
def delete_fondo_mutuo(id_fondo):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Eliminar el fondo mutuo
        cursor.execute("DELETE FROM FondosMutuos WHERE ID_Fondo = %s", (id_fondo,))
        conn.commit()
        flash("Fondo mutuo eliminado exitosamente.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al eliminar el fondo mutuo: {e}", "error")
    finally:
        cursor.close()
        conn.close()

    # Redirigir al listado de fondos mutuos
    return redirect(url_for('fondos_mutuos'))


@app.route('/boletas_garantia', methods=['GET'])
@login_required
def boletas_garantia():
    # Obtener parámetros de ordenamiento
    sort_by = request.args.get('sort_by', 'Numero')  # Ordenar por 'Numero' por defecto
    order = request.args.get('order', 'asc')  # Orden ascendente por defecto

    # Validar las columnas permitidas
    valid_columns = ['Numero', 'Banco', 'Beneficiario', 'Vencimiento', 'FechaEmision', 'Moneda', 'Monto', 'Estado']
    if sort_by not in valid_columns:
        sort_by = 'Numero'
    if order not in ['asc', 'desc']:
        order = 'asc'

    # Conectar a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()

    # Consulta SQL con ordenamiento dinámico
    query = f"""
        SELECT 
            bg.Numero, 
            e.Nombre AS Banco, 
            ec.Nombre AS Beneficiario, 
            bg.Vencimiento, 
            bg.FechaEmision, 
            bg.Moneda, 
            bg.Monto, 
            bg.Estado,
            bg.Documento
        FROM BoletaGarantia bg
        JOIN Entidad e ON bg.ID_Banco = e.ID_Entidad
        JOIN EntidadComercial ec ON bg.ID_Beneficiario = ec.ID_Entidad
        ORDER BY {sort_by} {order};
    """
    cursor.execute(query)
    boletas = cursor.fetchall()

    cursor.close()
    conn.close()

    # Renderizar la plantilla con las boletas y los parámetros de ordenamiento
    return render_template('boletas/boletas_garantia.html', boletas=boletas, sort_by=sort_by, order=order)

@app.route('/add_boleta_garantia', methods=['GET', 'POST'])
@login_required
def add_boleta_garantia():
    if request.method == 'POST':
        # Capturar datos del formulario
        numero_boleta = request.form['numero_boleta']
        tomada_por_empresa = request.form['tomada_por_empresa'].upper()
        tomada_por_rut = request.form['tomada_por_rut']
        banco_nombre = request.form['banco'].upper()
        beneficiario_nombre = request.form['beneficiario'].upper()
        glosa = request.form['glosa']
        vencimiento = request.form['vencimiento']
        fecha_emision = request.form['fecha_emision']
        moneda = request.form['moneda']
        monto = float(request.form['monto'])
        estado = request.form['estado']

        # Manejar archivo adjunto
        documento = None
        if 'documento' in request.files:
            file = request.files['documento']
            if file and allowed_file(file.filename):  # Verifica si es un archivo permitido
                filename = secure_filename(file.filename)
                documento = os.path.join(app.config['UPLOAD_FOLDER'], filename).replace("\\", "/")
                file.save(documento)

        # Conectar a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()

        # Buscar o crear banco
        cursor.execute("SELECT ID_Entidad FROM Entidad WHERE Nombre = %s", (banco_nombre,))
        banco_result = cursor.fetchone()
        if not banco_result:
            rut_temporal = f"TEMP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            cursor.execute("""
                INSERT INTO Entidad (Rut, Nombre, TipoEntidad)
                VALUES (%s, %s, 'Banco') RETURNING ID_Entidad
            """, (rut_temporal, banco_nombre))
            id_banco = cursor.fetchone()[0]
        else:
            id_banco = banco_result[0]

        # Buscar o crear beneficiario
        cursor.execute("SELECT ID_Entidad FROM EntidadComercial WHERE Nombre = %s", (beneficiario_nombre,))
        beneficiario_result = cursor.fetchone()
        if not beneficiario_result:
            rut_temporal = f"TEMP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            cursor.execute("""
                INSERT INTO EntidadComercial (Rut, Nombre, TipoEntidad)
                VALUES (%s, %s, 'Empresa') RETURNING ID_Entidad
            """, (rut_temporal, beneficiario_nombre))
            id_beneficiario = cursor.fetchone()[0]
        else:
            id_beneficiario = beneficiario_result[0]

        # Buscar o crear la empresa que tomó la boleta
        cursor.execute("""
            SELECT ID_Entidad FROM EntidadComercial WHERE Nombre = %s AND Rut = %s AND TipoEntidad = 'Empresa'
        """, (tomada_por_empresa, tomada_por_rut))
        tomada_por_result = cursor.fetchone()
        if not tomada_por_result:
            cursor.execute("""
                INSERT INTO EntidadComercial (Rut, Nombre, TipoEntidad)
                VALUES (%s, %s, 'Empresa') RETURNING ID_Entidad
            """, (tomada_por_rut, tomada_por_empresa))
            id_tomada_por = cursor.fetchone()[0]
        else:
            id_tomada_por = tomada_por_result[0]

        # Insertar boleta de garantía
        cursor.execute("""
            INSERT INTO BoletaGarantia 
            (Numero, ID_Banco, ID_Beneficiario, Glosa, Vencimiento, Moneda, Monto, FechaEmision, Estado, Documento, Tomada_Por_Empresa, Tomada_Por_Rut)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (numero_boleta ,id_banco, id_beneficiario, glosa, vencimiento, moneda, monto, fecha_emision, estado, documento, tomada_por_empresa, tomada_por_rut))
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('boletas_garantia'))

    return render_template('boletas/add_boleta_garantia.html')

@app.route('/edit_boleta_garantia/<int:numero>', methods=['GET', 'POST'])
@login_required
def edit_boleta_garantia(numero):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Capturar datos del formulario
        glosa = request.form['glosa']
        vencimiento = request.form['vencimiento']
        fecha_emision = request.form['fecha_emision']
        moneda = request.form['moneda']
        monto = float(request.form['monto'])
        estado = request.form['estado']

        # Manejar archivo adjunto
        documento = None
        if 'documento' in request.files:
            file = request.files['documento']
            if file and allowed_file(file.filename):  # Verifica si es un archivo permitido
                filename = secure_filename(file.filename)
                documento = os.path.join(app.config['UPLOAD_FOLDER'], filename).replace("\\", "/")
                file.save(documento)

        # Actualizar los datos en la base de datos
        query = """
            UPDATE BoletaGarantia
            SET Glosa = %s, Vencimiento = %s, FechaEmision = %s, Moneda = %s, 
                Monto = %s, Estado = %s, Documento = COALESCE(%s, Documento)
            WHERE Numero = %s
        """
        cursor.execute(query, (glosa, vencimiento, fecha_emision, moneda, monto, estado, documento, numero))
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('boletas_garantia'))

    # Obtener los datos actuales de la boleta para mostrarlos en el formulario
    query = "SELECT Glosa, Vencimiento, FechaEmision, Moneda, Monto, Estado FROM BoletaGarantia WHERE Numero = %s"
    cursor.execute(query, (numero,))
    boleta = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('boletas/edit_boleta_garantia.html', boleta=boleta, numero=numero)

@app.route('/delete_boleta_garantia/<int:numero>', methods=['POST'])
@login_required
def delete_boleta_garantia(numero):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Eliminar la boleta de garantía
        cursor.execute("DELETE FROM BoletaGarantia WHERE Numero = %s", (numero,))
        conn.commit()
        flash("Boleta de garantía eliminada exitosamente.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al eliminar la boleta de garantía: {e}", "error")
    finally:
        cursor.close()
        conn.close()

    # Redirigir al listado de boletas
    return redirect(url_for('boletas_garantia'))


@app.route('/polizas', methods=['GET'])
@login_required
def listar_polizas():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtener parámetros de ordenación desde la URL
    sort_by = request.args.get('sort_by', 'Numero')  # Columna por defecto: 'Numero'
    order = request.args.get('order', 'asc')  # Orden por defecto: ascendente

    # Validar columnas permitidas para evitar SQL injection
    valid_columns = ['Numero', 'TipoAsegurado', 'FechaInicio', 'FechaTermino', 'Monto']
    if sort_by not in valid_columns:
        sort_by = 'Numero'
    if order not in ['asc', 'desc']:
        order = 'asc'

    # Consultar pólizas existentes con orden dinámico
    query = f"SELECT * FROM Polizas ORDER BY {sort_by} {order}"
    cursor.execute(query)
    polizas = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('polizas/polizas.html', polizas=polizas, sort_by=sort_by, order=order)

@app.route('/add_poliza', methods=['GET', 'POST'])
@login_required
def agregar_poliza():
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Capturar datos del formulario
            numero = request.form['numero']  # Corregido: Debe coincidir con el formulario
            tipo_asegurado = request.form['tipo_asegurado']
            fecha_inicio = request.form['fecha_inicio']
            fecha_termino = request.form['fecha_termino']
            monto = float(request.form['monto'])

            # Manejo del archivo adjunto
            adjunto_poliza = None
            if 'adjunto_poliza' in request.files:
                file = request.files['adjunto_poliza']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    adjunto_poliza = os.path.join(app.config['UPLOAD_FOLDER'], filename).replace("\\", "/")
                    file.save(adjunto_poliza)

            # Validar si el número de póliza ya existe
            cursor.execute("SELECT 1 FROM Polizas WHERE Numero = %s", (numero,))
            if cursor.fetchone():
                flash("El número de póliza ya existe. Por favor, ingrese otro.", "error")
                return redirect(url_for('agregar_poliza'))
            
            if fecha_inicio > fecha_termino:
                flash("La fecha de inicio no puede ser posterior a la fecha de término.", "error")
                return redirect(url_for('agregar_poliza'))

            # Insertar en la base de datos
            cursor.execute("""
                INSERT INTO Polizas (Numero, TipoAsegurado, FechaInicio, FechaTermino, Monto, AdjuntoPoliza)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (numero, tipo_asegurado, fecha_inicio, fecha_termino, monto, adjunto_poliza))

            conn.commit()
            flash('Póliza agregada exitosamente.', 'success')

        except Exception as e:
            conn.rollback()
            flash(f'Error al agregar la póliza: {e}', 'error')
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('listar_polizas'))

    return render_template('polizas/add_polizas.html')

@app.route('/edit_poliza/<int:numero>', methods=['GET', 'POST'])
@login_required
def editar_poliza(numero):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        try:
            # Capturar datos del formulario
            tipo_asegurado = request.form['tipo_asegurado']
            fecha_inicio = request.form['fecha_inicio']
            fecha_termino = request.form['fecha_termino']
            monto = float(request.form['monto'])

            # Manejo del archivo adjunto
            adjunto_poliza = None
            if 'adjunto_poliza' in request.files:
                file = request.files['adjunto_poliza']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    adjunto_poliza = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(adjunto_poliza)

            # Actualizar en la base de datos
            cursor.execute("""
                UPDATE Polizas
                SET TipoAsegurado = %s, FechaInicio = %s, FechaTermino = %s, Monto = %s, AdjuntoPoliza = %s
                WHERE Numero = %s
            """, (tipo_asegurado, fecha_inicio, fecha_termino, monto, adjunto_poliza, numero))

            conn.commit()
            flash('Póliza actualizada exitosamente.', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Error al actualizar la póliza: {e}', 'error')
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('listar_polizas'))

    # Obtener datos de la póliza actual
    cursor.execute("SELECT * FROM Polizas WHERE Numero = %s", (numero,))
    poliza = cursor.fetchone()
    cursor.close()
    conn.close()

    if not poliza:
        flash('La póliza no existe.', 'error')
        return redirect(url_for('listar_polizas'))

    return render_template('polizas/edit_polizas.html', poliza=poliza)

@app.route('/delete_poliza/<int:numero>', methods=['POST'])
@login_required
def eliminar_poliza(numero):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Eliminar la póliza de la base de datos
        cursor.execute("DELETE FROM Polizas WHERE Numero = %s", (numero,))
        conn.commit()
        flash('Póliza eliminada exitosamente.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error al eliminar la póliza: {e}', 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('listar_polizas'))

@app.route('/bancos', methods=['GET'])
@login_required
def listar_bancos():
    """
    Muestra un listado de todos los bancos registrados en la base de datos.
    """
    try:
        # Conectar a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()

        # Consultar todos los bancos
        cursor.execute("""
            SELECT ID_Entidad, Rut, Nombre, FonoMovil, Email
            FROM Entidad
            WHERE TipoEntidad = 'Banco'
            ORDER BY Nombre ASC
            """)
        bancos = cursor.fetchall()

    except Exception as e:
        flash(f"Error al obtener los datos de los bancos: {e}", "error")
        bancos = []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    # Renderizar la plantilla con los bancos
    return render_template('configuracion/bancos/bancos.html', bancos=bancos)

@app.route('/delete_banco/<int:id_banco>', methods=['POST'])
@login_required
def delete_banco(id_banco):
    print(f"Entrando a delete_banco con ID: {id_banco}")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Comprobar si el banco existe antes de eliminar
        cursor.execute("SELECT * FROM Entidad WHERE ID_Entidad = %s AND TipoEntidad = 'Banco'", (id_banco,))
        banco = cursor.fetchone()
        if not banco:
            flash("El banco no existe o no es del tipo 'Banco'.", "error")
            return redirect(url_for('listar_bancos'))

        # Intentar eliminar el banco
        cursor.execute("DELETE FROM Entidad WHERE ID_Entidad = %s AND TipoEntidad = 'Banco'", (id_banco,))
        conn.commit()

        print(f"Banco eliminado: {id_banco}")
        flash("Banco eliminado exitosamente.", "success")
    except Exception as e:
        conn.rollback()
        print(f"Error al eliminar: {e}")
        flash(f"Error al eliminar el banco: {e}", "error")
    finally:
        cursor.close()
        conn.close()

    # Redirigir al listado de bancos después de la eliminación
    return redirect(url_for('listar_bancos'))

@app.route('/bancos/add', methods=['GET', 'POST'])
@login_required
def add_banco():
    if request.method == 'POST':
        # Capturar datos del formulario
        rut = request.form['rut']
        nombre = request.form['nombre'].upper()
        email = request.form.get('email')  # Opcional
        fono_fijo = request.form.get('fono_fijo')  # Opcional
        fono_movil = request.form.get('fono_movil')  # Opcional

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Insertar en la tabla Entidad con TipoEntidad = 'Banco'
            cursor.execute("""
                INSERT INTO Entidad (Rut, Nombre, Email, FonoFijo, FonoMovil, TipoEntidad)
                VALUES (%s, %s, %s, %s, %s, 'Banco')
            """, (rut, nombre, email, fono_fijo, fono_movil))
            conn.commit()

            flash("Banco agregado exitosamente.", "success")
            return redirect(url_for('listar_bancos'))
        except Exception as e:
            conn.rollback()
            flash(f"Error al agregar el banco: {e}", "error")
        finally:
            cursor.close()
            conn.close()

    return render_template('configuracion/bancos/add_bancos.html')

@app.route('/bancos/edit/<int:id_banco>', methods=['GET', 'POST'])
@login_required
def edit_banco(id_banco):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'POST':
            # Capturar datos del formulario
            rut = request.form['rut']
            nombre = request.form['nombre']
            email = request.form.get('email')  # Opcional
            fono_fijo = request.form.get('fono_fijo')  # Opcional
            fono_movil = request.form.get('fono_movil')  # Opcional

            # Actualizar el banco
            cursor.execute("""
                UPDATE Entidad
                SET Rut = %s, Nombre = %s, Email = %s, FonoFijo = %s, FonoMovil = %s
                WHERE ID_Entidad = %s AND TipoEntidad = 'Banco'
            """, (rut, nombre, email, fono_fijo, fono_movil, id_banco))
            conn.commit()

            flash("Banco actualizado exitosamente.", "success")
            return redirect(url_for('listar_bancos'))

        # Obtener los datos actuales del banco
        cursor.execute("""
            SELECT Rut, Nombre, Email, FonoFijo, FonoMovil
            FROM Entidad
            WHERE ID_Entidad = %s AND TipoEntidad = 'Banco'
        """, (id_banco,))
        banco = cursor.fetchone()

        if not banco:
            flash("Banco no encontrado.", "error")
            return redirect(url_for('listar_bancos'))

    except Exception as e:
        if conn:
            conn.rollback()
        flash(f"Error al procesar la solicitud: {e}", "error")
        return redirect(url_for('listar_bancos'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template('configuracion/bancos/edit_banco.html', banco=banco, id_banco=id_banco)

@app.route('/empresas', methods=['GET'])
@login_required
def listar_empresas():
    """
    Muestra un listado de todas las empresas registrados en la base de datos.
    """
    try:
        # Conectar a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()

        # Consultar todos las empresas
        cursor.execute("""
            SELECT ID_Entidad, Rut, Nombre, FonoMovil, Email
            FROM EntidadComercial
            WHERE TipoEntidad = 'Empresa'
            ORDER BY Nombre ASC
            """)
        empresas = cursor.fetchall()

    except Exception as e:
        flash(f"Error al obtener los datos de las empresas: {e}", "error")
        empresas = []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    # Renderizar la plantilla con las empresas
    return render_template('configuracion/empresas/empresas.html', empresas=empresas)

@app.route('/empresas/add', methods=['GET', 'POST'])
@login_required
def add_empresa():
    if request.method == 'POST':
        # Capturar datos del formulario
        rut = request.form['rut']
        nombre = request.form['nombre'].upper()
        fono_fijo = request.form['fono_fijo']
        fono_movil = request.form['fono_movil']
        email = request.form['email']

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Insertar en la tabla Entidad con TipoEntidad = 'Banco'
            cursor.execute("""
                INSERT INTO EntidadComercial (Rut, Nombre, FonoFijo, FonoMovil, Email, TipoEntidad)
                VALUES (%s, %s, %s, %s, %s, 'Empresa')
            """, (rut, nombre, fono_fijo, fono_movil, email))
            conn.commit()

            flash("Empresa agregada exitosamente.", "success")
            return redirect(url_for('listar_empresas'))
        except Exception as e:
            conn.rollback()
            flash(f"Error al agregar la empresa: {e}", "error")
        finally:
            cursor.close()
            conn.close()

    return render_template('configuracion/empresas/add_empresas.html')

@app.route('/delete_empresa/<int:id_empresa>', methods=['POST'])
@login_required
def delete_empresa(id_empresa):
    print(f"Entrando a delete_empresa con ID: {id_empresa}")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Comprobar si el banco existe antes de eliminar
        cursor.execute("SELECT * FROM EntidadComercial WHERE ID_Entidad = %s AND TipoEntidad = 'Empresa'", (id_empresa,))
        empresa = cursor.fetchone()
        if not empresa:
            flash("La empresa no existe o no es del tipo 'Banco'.", "error")
            return redirect(url_for('listar_empresas'))

        # Intentar eliminar el banco
        cursor.execute("DELETE FROM EntidadComercial WHERE ID_Entidad = %s AND TipoEntidad = 'Empresa'", (id_empresa,))
        conn.commit()

        print(f"Empresa eliminada: {id_empresa}")
        flash("Empresa eliminada exitosamente.", "success")
    except Exception as e:
        conn.rollback()
        print(f"Error al eliminar: {e}")
        flash(f"Error al eliminar la empresa: {e}", "error")
    finally:
        cursor.close()
        conn.close()

    # Redirigir al listado de bancos después de la eliminación
    return redirect(url_for('listar_empresas'))

@app.route('/empresas/edit/<int:id_empresa>', methods=['GET', 'POST'])
@login_required
def edit_empresa(id_empresa):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'POST':
            # Capturar datos del formulario
            rut = request.form['rut']
            nombre = request.form['nombre']
            email = request.form.get('email')  # Opcional
            fono_fijo = request.form.get('fono_fijo')  # Opcional
            fono_movil = request.form.get('fono_movil')  # Opcional

            # Actualizar el banco
            cursor.execute("""
                UPDATE EntidadComercial
                SET Rut = %s, Nombre = %s, Email = %s, FonoFijo = %s, FonoMovil = %s
                WHERE ID_Entidad = %s AND TipoEntidad = 'Empresa'
            """, (rut, nombre, email, fono_fijo, fono_movil, id_empresa))
            conn.commit()

            flash("Empresa actualizado exitosamente.", "success")
            return redirect(url_for('listar_empresas'))

        # Obtener los datos actuales del banco
        cursor.execute("""
            SELECT Rut, Nombre, Email, FonoFijo, FonoMovil
            FROM EntidadComercial
            WHERE ID_Entidad = %s AND TipoEntidad = 'Empresa'
        """, (id_empresa,))
        empresa = cursor.fetchone()

        if not empresa:
            flash("Empresa no encontrada.", "error")
            return redirect(url_for('listar_empresas'))

    except Exception as e:
        if conn:
            conn.rollback()
        flash(f"Error al procesar la solicitud: {e}", "error")
        return redirect(url_for('listar_empresas'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template('configuracion/empresas/edit_empresa.html', empresa=empresa, id_empresa=id_empresa)

@app.route('/corredores', methods=['GET'])
@login_required
def listar_corredores():
    """
    Muestra un listado de todos los corredores registrados en la base de datos.
    """
    try:
        # Conectar a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()

        # Consultar todos los corredores
        cursor.execute("""
            SELECT ID_Entidad, Rut, Nombre, FonoMovil, Email
            FROM Entidad
            WHERE TipoEntidad = 'Corredor'
            ORDER BY Nombre ASC
            """)
        corredores = cursor.fetchall()

    except Exception as e:
        flash(f"Error al obtener los datos de los corredores: {e}", "error")
        corredores = []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    # Renderizar la plantilla con los corredores
    return render_template('configuracion/corredores/corredores.html', corredores=corredores)

@app.route('/corredores/add', methods=['GET', 'POST'])
@login_required
def add_corredor():
    if request.method == 'POST':
        # Capturar datos del formulario
        rut = request.form['rut']
        nombre = request.form['nombre'].upper()
        email = request.form.get('email')  # Opcional
        fono_fijo = request.form.get('fono_fijo')  # Opcional
        fono_movil = request.form.get('fono_movil')  # Opcional

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Insertar en la tabla Entidad con TipoEntidad = 'Corredor'
            cursor.execute("""
                INSERT INTO Entidad (Rut, Nombre, Email, FonoFijo, FonoMovil, TipoEntidad)
                VALUES (%s, %s, %s, %s, %s, 'Corredor')
            """, (rut, nombre, email, fono_fijo, fono_movil))
            conn.commit()

            flash("Corredor agregado exitosamente.", "success")
            return redirect(url_for('listar_corredores'))
        except Exception as e:
            conn.rollback()
            flash(f"Error al agregar el corredor: {e}", "error")
        finally:
            cursor.close()
            conn.close()

    return render_template('configuracion/corredores/add_corredores.html')

@app.route('/delete_corredor/<int:id_corredor>', methods=['POST'])
@login_required
def delete_corredor(id_corredor):
    print(f"Entrando a delete_corredor con ID: {id_corredor}")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Comprobar si el corredor existe antes de eliminar
        cursor.execute("SELECT * FROM Entidad WHERE ID_Entidad = %s AND TipoEntidad = 'Corredor'", (id_corredor,))
        corredor = cursor.fetchone()
        if not corredor:
            flash("El corredor no existe o no es del tipo 'Corredor'.", "error")
            return redirect(url_for('listar_corredors'))

        # Intentar eliminar el corredor
        cursor.execute("DELETE FROM Entidad WHERE ID_Entidad = %s AND TipoEntidad = 'Corredor'", (id_corredor,))
        conn.commit()

        print(f"Corredor eliminado: {id_corredor}")
        flash("Corredor eliminado exitosamente.", "success")
    except Exception as e:
        conn.rollback()
        print(f"Error al eliminar: {e}")
        flash(f"Error al eliminar el corredor: {e}", "error")
    finally:
        cursor.close()
        conn.close()

    # Redirigir al listado de corredores después de la eliminación
    return redirect(url_for('listar_corredores'))

@app.route('/corredores/edit/<int:id_corredor>', methods=['GET', 'POST'])
@login_required
def edit_corredor(id_corredor):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'POST':
            # Capturar datos del formulario
            rut = request.form['rut']
            nombre = request.form['nombre']
            email = request.form.get('email')  # Opcional
            fono_fijo = request.form.get('fono_fijo')  # Opcional
            fono_movil = request.form.get('fono_movil')  # Opcional

            # Actualizar el corredor
            cursor.execute("""
                UPDATE Entidad
                SET Rut = %s, Nombre = %s, Email = %s, FonoFijo = %s, FonoMovil = %s
                WHERE ID_Entidad = %s AND TipoEntidad = 'Corredor'
            """, (rut, nombre, email, fono_fijo, fono_movil, id_corredor))
            conn.commit()

            flash("Corredor actualizado exitosamente.", "success")
            return redirect(url_for('listar_corredores'))

        # Obtener los datos actuales del corredor
        cursor.execute("""
            SELECT Rut, Nombre, Email, FonoFijo, FonoMovil
            FROM Entidad
            WHERE ID_Entidad = %s AND TipoEntidad = 'Corredor'
        """, (id_corredor,))
        corredor = cursor.fetchone()

        if not corredor:
            flash("Corredor no encontrado.", "error")
            return redirect(url_for('listar_corredores'))

    except Exception as e:
        if conn:
            conn.rollback()
        flash(f"Error al procesar la solicitud: {e}", "error")
        return redirect(url_for('listar_corredores'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template('configuracion/corredores/edit_corredores.html', corredor=corredor, id_corredor=id_corredor)

@app.route('/clientes', methods=['GET'])
@login_required
def listar_clientes():
    """
    Muestra un listado de todas las clientes registrados en la base de datos.
    """
    try:
        # Conectar a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()

        # Consultar todos las clientes
        cursor.execute("""
            SELECT ID_Entidad, Rut, Nombre, FonoMovil, Email
            FROM EntidadComercial
            WHERE TipoEntidad = 'Cliente'
            ORDER BY Nombre ASC
            """)
        clientes = cursor.fetchall()

    except Exception as e:
        flash(f"Error al obtener los datos de las clientes: {e}", "error")
        clientes = []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    # Renderizar la plantilla con las clientes
    return render_template('configuracion/clientes/clientes.html', clientes=clientes)

@app.route('/clientes/add', methods=['GET', 'POST'])
@login_required
def add_cliente():
    if request.method == 'POST':
        # Capturar datos del formulario
        rut = request.form['rut']
        nombre = request.form['nombre'].upper()
        fono_fijo = request.form['fono_fijo']
        fono_movil = request.form['fono_movil']
        email = request.form['email']

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Insertar en la tabla Entidad con TipoEntidad = 'Banco'
            cursor.execute("""
                INSERT INTO EntidadComercial (Rut, Nombre, FonoFijo, FonoMovil, Email, TipoEntidad)
                VALUES (%s, %s, %s, %s, %s, 'Cliente')
            """, (rut, nombre, fono_fijo, fono_movil, email))
            conn.commit()

            flash("Cliente agregada exitosamente.", "success")
            return redirect(url_for('listar_clientes'))
        except Exception as e:
            conn.rollback()
            flash(f"Error al agregar la cliente: {e}", "error")
        finally:
            cursor.close()
            conn.close()

    return render_template('configuracion/clientes/add_clientes.html')

@app.route('/clientes/edit/<int:id_cliente>', methods=['GET', 'POST'])
@login_required
def edit_cliente(id_cliente):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'POST':
            # Capturar datos del formulario
            rut = request.form['rut']
            nombre = request.form['nombre']
            email = request.form.get('email')  # Opcional
            fono_fijo = request.form.get('fono_fijo')  # Opcional
            fono_movil = request.form.get('fono_movil')  # Opcional

            # Actualizar el banco
            cursor.execute("""
                UPDATE EntidadComercial
                SET Rut = %s, Nombre = %s, Email = %s, FonoFijo = %s, FonoMovil = %s
                WHERE ID_Entidad = %s AND TipoEntidad = 'Cliente'
            """, (rut, nombre, email, fono_fijo, fono_movil, id_cliente))
            conn.commit()

            flash("Cliente actualizado exitosamente.", "success")
            return redirect(url_for('listar_clientes'))

        # Obtener los datos actuales del banco
        cursor.execute("""
            SELECT Rut, Nombre, Email, FonoFijo, FonoMovil
            FROM EntidadComercial
            WHERE ID_Entidad = %s AND TipoEntidad = 'Cliente'
        """, (id_cliente,))
        cliente = cursor.fetchone()

        if not cliente:
            flash("Cliente no encontrada.", "error")
            return redirect(url_for('listar_clientes'))

    except Exception as e:
        if conn:
            conn.rollback()
        flash(f"Error al procesar la solicitud: {e}", "error")
        return redirect(url_for('listar_clientes'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template('configuracion/clientes/edit_clientes.html', cliente=cliente, id_cliente=id_cliente)

@app.route('/delete_cliente/<int:id_cliente>', methods=['POST'])
@login_required
def delete_cliente(id_cliente):
    print(f"Entrando a delete_cliente con ID: {id_cliente}")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Comprobar si el banco existe antes de eliminar
        cursor.execute("SELECT * FROM EntidadComercial WHERE ID_Entidad = %s AND TipoEntidad = 'Cliente'", (id_cliente,))
        cliente = cursor.fetchone()
        if not cliente:
            flash("La cliente no existe o no es del tipo 'Banco'.", "error")
            return redirect(url_for('listar_clientes'))

        # Intentar eliminar el banco
        cursor.execute("DELETE FROM EntidadComercial WHERE ID_Entidad = %s AND TipoEntidad = 'Cliente'", (id_cliente,))
        conn.commit()

        print(f"Cliente eliminada: {id_cliente}")
        flash("Cliente eliminada exitosamente.", "success")
    except Exception as e:
        conn.rollback()
        print(f"Error al eliminar: {e}")
        flash(f"Error al eliminar la cliente: {e}", "error")
    finally:
        cursor.close()
        conn.close()

    # Redirigir al listado de bancos después de la eliminación
    return redirect(url_for('listar_clientes'))

@app.route('/companias', methods=['GET'])
@login_required
def listar_companias():
    """
    Muestra un listado de todos los companias registrados en la base de datos.
    """
    try:
        # Conectar a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()

        # Consultar todos los companias
        cursor.execute("""
            SELECT ID_Entidad, Rut, Nombre, FonoMovil, Email
            FROM Entidad
            WHERE TipoEntidad = 'Compania'
            ORDER BY Nombre ASC
            """)
        companias = cursor.fetchall()

    except Exception as e:
        flash(f"Error al obtener los datos de los companias: {e}", "error")
        companias = []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    # Renderizar la plantilla con los companias
    return render_template('configuracion/companias/companias.html', companias=companias)

@app.route('/companias/add', methods=['GET', 'POST'])
@login_required
def add_compania():
    if request.method == 'POST':
        # Capturar datos del formulario
        rut = request.form['rut']
        nombre = request.form['nombre'].upper()
        email = request.form.get('email')  # Opcional
        fono_fijo = request.form.get('fono_fijo')  # Opcional
        fono_movil = request.form.get('fono_movil')  # Opcional

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Insertar en la tabla Entidad con TipoEntidad = 'compania'
            cursor.execute("""
                INSERT INTO Entidad (Rut, Nombre, Email, FonoFijo, FonoMovil, TipoEntidad)
                VALUES (%s, %s, %s, %s, %s, 'Compania')
            """, (rut, nombre, email, fono_fijo, fono_movil))
            conn.commit()

            flash("Compania agregado exitosamente.", "success")
            return redirect(url_for('listar_companias'))
        except Exception as e:
            conn.rollback()
            flash(f"Error al agregar el compania: {e}", "error")
        finally:
            cursor.close()
            conn.close()

    return render_template('configuracion/companias/add_companias.html')

@app.route('/delete_compania/<int:id_compania>', methods=['POST'])
@login_required
def delete_compania(id_compania):
    print(f"Entrando a delete_compania con ID: {id_compania}")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Comprobar si el compania existe antes de eliminar
        cursor.execute("SELECT * FROM Entidad WHERE ID_Entidad = %s AND TipoEntidad = 'Compania'", (id_compania,))
        compania = cursor.fetchone()
        if not compania:
            flash("El compania no existe o no es del tipo 'Compania'.", "error")
            return redirect(url_for('listar_companias'))

        # Intentar eliminar el compania
        cursor.execute("DELETE FROM Entidad WHERE ID_Entidad = %s AND TipoEntidad = 'Compania'", (id_compania,))
        conn.commit()

        print(f"Compania eliminado: {id_compania}")
        flash("Compania eliminado exitosamente.", "success")
    except Exception as e:
        conn.rollback()
        print(f"Error al eliminar: {e}")
        flash(f"Error al eliminar el compania: {e}", "error")
    finally:
        cursor.close()
        conn.close()

    # Redirigir al listado de companias después de la eliminación
    return redirect(url_for('listar_companias'))

@app.route('/companias/edit/<int:id_compania>', methods=['GET', 'POST'])
@login_required
def edit_compania(id_compania):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'POST':
            # Capturar datos del formulario
            rut = request.form['rut']
            nombre = request.form['nombre']
            email = request.form.get('email')  # Opcional
            fono_fijo = request.form.get('fono_fijo')  # Opcional
            fono_movil = request.form.get('fono_movil')  # Opcional

            # Actualizar el compania
            cursor.execute("""
                UPDATE Entidad
                SET Rut = %s, Nombre = %s, Email = %s, FonoFijo = %s, FonoMovil = %s
                WHERE ID_Entidad = %s AND TipoEntidad = 'Compania'
            """, (rut, nombre, email, fono_fijo, fono_movil, id_compania))
            conn.commit()

            flash("Compania actualizado exitosamente.", "success")
            return redirect(url_for('listar_companias'))

        # Obtener los datos actuales del compania
        cursor.execute("""
            SELECT Rut, Nombre, Email, FonoFijo, FonoMovil
            FROM Entidad
            WHERE ID_Entidad = %s AND TipoEntidad = 'Compania'
        """, (id_compania,))
        compania = cursor.fetchone()

        if not compania:
            flash("Compania no encontrado.", "error")
            return redirect(url_for('listar_companias'))

    except Exception as e:
        if conn:
            conn.rollback()
        flash(f"Error al procesar la solicitud: {e}", "error")
        return redirect(url_for('listar_companias'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template('configuracion/companias/edit_companias.html', compania=compania, id_compania=id_compania)

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run(debug=True)