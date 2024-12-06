from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from database import get_db_connection
from werkzeug.utils import secure_filename
from helpers.utils import allowed_file
from datetime import datetime
from flask import current_app
import os

# Crear el Blueprint
boletas_garantia_bp = Blueprint('boletas_garantia_bp', __name__)

@boletas_garantia_bp.route('/boletas_garantia', methods=['GET'])
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

@boletas_garantia_bp.route('/add_boleta_garantia', methods=['GET', 'POST'])
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
                documento = os.path.join(current_app.config['UPLOAD_FOLDER'], filename).replace("\\", "/")
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

@boletas_garantia_bp.route('/edit_boleta_garantia/<int:numero>', methods=['GET', 'POST'])
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
                documento = os.path.join(current_app.config['UPLOAD_FOLDER'], filename).replace("\\", "/")
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

@boletas_garantia_bp.route('/delete_boleta_garantia/<int:numero>', methods=['POST'])
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