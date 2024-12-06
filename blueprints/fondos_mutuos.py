from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from database import get_db_connection
from werkzeug.utils import secure_filename
from datetime import datetime
from helpers.utils import allowed_file
from flask import current_app
import os

# Crear el Blueprint
fondos_mutuos_bp = Blueprint('fondos_mutuos', __name__)


@fondos_mutuos_bp.route('/fondos_mutuos', methods=['GET'])
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

@fondos_mutuos_bp.route('/add_fondo_mutuo', methods=['GET', 'POST'])
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
                comprobante = os.path.join(current_app.config['UPLOAD_FOLDER'], filename).replace("\\", "/")
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

@fondos_mutuos_bp.route('/edit_fondo_mutuo/<int:id_fondo>', methods=['GET', 'POST'])
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

@fondos_mutuos_bp.route('/delete_fondo_mutuo/<int:id_fondo>', methods=['POST'])
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