from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
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
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        try:
            print(request.form)  # Debug
            # Capturar datos del formulario
            nombre_fondo = request.form['nombre_fondo'].upper()
            monto_invertido = float(request.form.get('monto_invertido'))
            monto_final = request.form.get('monto_final')
            if monto_final:
                monto_final = float(monto_final)
            else:
                monto_final = None  # Para valores nulos en SQL
            riesgo = request.form['riesgo']
            fecha_inicio = request.form['fecha_inicio']
            fecha_termino = request.form.get('fecha_termino')
            if not fecha_termino:
                fecha_termino = None

            # IDs seleccionados de empresa y banco
            id_empresa = request.form['nombre_empresa']
            id_banco = request.form['nombre_banco']

            # Manejar archivo comprobante
            documento = None
            if 'comprobante' in request.files:
                file = request.files['comprobante']
                if file and file.filename != '':
                    # Asegurar nombre del archivo
                    filename = secure_filename(file.filename)
                    documento = os.path.join('static/uploads', filename)
                    file.save(documento)

            # Insertar fondo mutuo en la base de datos
            cursor.execute("""
                INSERT INTO FondosMutuos 
                (Nombre, MontoInvertido, MontoFinal, Rentabilidad, TipoRiesgo, FechaInicio, FechaTermino, ID_Entidad, ID_Banco, Comprobante)
                VALUES (%s, %s, %s, NULL, %s, %s, %s, %s, %s, %s)
            """, (nombre_fondo, monto_invertido, monto_final, riesgo, fecha_inicio, fecha_termino, id_empresa, id_banco, documento))
            conn.commit()

            flash("Fondo Mutuo agregado exitosamente.", "success")
            return redirect(url_for('fondos_mutuos.fondos_mutuos'))

        except Exception as e:
            conn.rollback()
            flash(f"Error al agregar el fondo mutuo: {e}", "error")

    # Cargar empresas y bancos para los selects
    try:
        cursor.execute("SELECT ID_Entidad, Nombre FROM EntidadComercial WHERE TipoEntidad = 'Empresa'")
        empresas = cursor.fetchall()

        cursor.execute("SELECT ID_Entidad, Nombre FROM Entidad WHERE TipoEntidad = 'Banco'")
        bancos = cursor.fetchall()
    except Exception as e:
        flash(f"Error al cargar empresas o bancos: {e}", "error")
        empresas = []
        bancos = []

    finally:
        cursor.close()
        conn.close()

    return render_template('fondos/add_fondo_mutuo.html', empresas=empresas, bancos=bancos)


@fondos_mutuos_bp.route('/edit_fondo_mutuo/<int:id_fondo>', methods=['GET', 'POST'])
@login_required
def edit_fondo_mutuo(id_fondo):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Capturar datos del formulario
        id_empresa = request.form['nombre_empresa']
        id_banco = request.form['nombre_banco']
        nombre_fondo = request.form['nombre_fondo'].upper()
        monto_invertido = float(request.form['monto_invertido'])
        monto_final = request.form.get('monto_final')
        monto_final = float(monto_final) if monto_final else None
        tipo_riesgo = request.form['riesgo']
        fecha_inicio = request.form['fecha_inicio']
        fecha_termino = request.form.get('fecha_termino')

        # Manejo del archivo adjunto
        documento = None
        if 'comprobante' in request.files:
            file = request.files['comprobante']
            if file and file.filename != '':
                # Si hay un nuevo archivo, lo guardamos
                filename = secure_filename(file.filename)
                documento = os.path.join('static/uploads', filename)
                file.save(documento)
            else:
                # Si no se adjunta un nuevo archivo, conservar el archivo actual
                cursor.execute("SELECT Comprobante FROM FondosMutuos WHERE ID_Fondo = %s", (id_fondo,))
                documento = cursor.fetchone()[0]

        try:
            # Actualizar el fondo mutuo en la base de datos
            cursor.execute("""
                UPDATE FondosMutuos
                SET ID_Entidad = %s, ID_Banco = %s, Nombre = %s, MontoInvertido = %s,
                    MontoFinal = %s, TipoRiesgo = %s, FechaInicio = %s, FechaTermino = %s, Comprobante = %s
                WHERE ID_Fondo = %s
            """, (id_empresa, id_banco, nombre_fondo, monto_invertido, monto_final,
                  tipo_riesgo, fecha_inicio, fecha_termino, documento, id_fondo))

            conn.commit()
            flash('Fondo mutuo actualizado exitosamente.', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Error al actualizar el fondo mutuo: {e}', 'error')
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('fondos_mutuos.fondos_mutuos'))

    # Si es GET, cargar los datos existentes del fondo
    cursor.execute("""
        SELECT fm.ID_Entidad, fm.ID_Banco, fm.Nombre, fm.MontoInvertido, fm.MontoFinal, 
               fm.TipoRiesgo, fm.FechaInicio, fm.FechaTermino, fm.Comprobante,
               e.Nombre AS Empresa, b.Nombre AS Banco
        FROM FondosMutuos fm
        JOIN EntidadComercial e ON fm.ID_Entidad = e.ID_Entidad
        JOIN Entidad b ON fm.ID_Banco = b.ID_Entidad
        WHERE fm.ID_Fondo = %s
    """, (id_fondo,))
    fondo = cursor.fetchone()

    # Obtener datos para los selects
    cursor.execute("SELECT ID_Entidad, Nombre FROM EntidadComercial WHERE TipoEntidad = 'Empresa'")
    empresas = cursor.fetchall()
    cursor.execute("SELECT ID_Entidad, Nombre FROM Entidad WHERE TipoEntidad = 'Banco'")
    bancos = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('fondos/edit_fondo_mutuo.html', fondo=fondo, empresas=empresas, bancos=bancos)




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
    return redirect(url_for('fondos_mutuos.fondos_mutuos'))


@fondos_mutuos_bp.route('/agregar_entidad', methods=['POST'])
def agregar_entidad():
    try:
        data = request.json
        rut = data['rut']
        nombre = data['nombre']
        tipo_entidad = data['tipo_entidad']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insertar según el tipo de entidad
        if tipo_entidad == "Banco":
            cursor.execute("""
                INSERT INTO Entidad (Rut, Nombre, TipoEntidad) 
                VALUES (%s, %s, 'Banco') RETURNING ID_Entidad
            """, (rut, nombre))
        elif tipo_entidad == "Empresa":
            cursor.execute("""
                INSERT INTO EntidadComercial (Rut, Nombre, TipoEntidad) 
                VALUES (%s, %s, 'Empresa') RETURNING ID_Entidad
            """, (rut, nombre))
        else:
            return jsonify({"success": False, "error": "Tipo de entidad inválido"}), 400

        entidad_id = cursor.fetchone()[0]
        conn.commit()

        return jsonify({"success": True, "id": entidad_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
