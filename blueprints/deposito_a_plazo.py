from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from database import get_db_connection
from werkzeug.utils import secure_filename
from helpers.utils import allowed_file
from datetime import datetime
from flask import current_app
import os

# Crear el Blueprint
deposito_a_plazo_bp = Blueprint('deposito_a_plazo', __name__)

@deposito_a_plazo_bp.route('/deposito_a_plazo', methods=['GET'])
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

@deposito_a_plazo_bp.route('/add_deposito', methods=['GET', 'POST'])
@login_required
def add_deposito():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        try:
            # Capturar datos del formulario
            id_deposito = request.form['numero_deposito']
            tipo = request.form['tipo']
            monto = float(request.form['monto'])
            fecha_emision = request.form['fecha_emision']
            tasa_interes = float(request.form['tasa_interes'])
            fecha_vencimiento = request.form['fecha_vencimiento']
            moneda = request.form.get('moneda', 'CLP')
            interes_ganado = float(request.form.get('interes_ganado', 0))
            id_banco = request.form['nombre_banco']
            id_beneficiario = request.form['id_beneficiario']

            # Validar campos de renovación solo si el tipo es "Renovable"
            if tipo == "Renovable":
                capital_renovacion = float(request.form.get('capital_renovacion', 0))
                fecha_emision_renovacion = request.form.get('fecha_emision_renovacion')
                tasa_interes_renovacion = float(request.form.get('tasa_interes_renovacion', 0))
                plazo_renovacion = int(request.form.get('plazo_renovacion', 0))
                tasa_periodo = float(request.form.get('tasa_periodo', 0))
                fecha_vencimiento_renovacion = request.form.get('fecha_vencimiento_renovacion')
                total_pagar_renovacion = float(request.form.get('total_pagar_renovacion', 0))
            else:
                # Si no es renovable, estos campos no se guardan
                capital_renovacion = None
                fecha_emision_renovacion = None
                tasa_interes_renovacion = None
                plazo_renovacion = None
                tasa_periodo = None
                fecha_vencimiento_renovacion = None
                total_pagar_renovacion = None

            # Manejo del archivo comprobante
            comprobante = None
            if 'comprobante' in request.files and request.files['comprobante'].filename != '':
                file = request.files['comprobante']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    relative_path = os.path.join('static', 'uploads', filename)
                    comprobante_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    os.makedirs(os.path.dirname(comprobante_path), exist_ok=True)
                    file.save(comprobante_path)
                    comprobante = relative_path

            # Insertar el depósito en la base de datos
            cursor.execute("""
                INSERT INTO DepositoAPlazo (
                    ID_Deposito, ID_Banco, ID_EntidadComercial, FechaEmision, FechaVencimiento, Moneda, MontoInicial, TipoDeposito, 
                    InteresGanado, TasaInteres, CapitalRenovacion, FechaEmisionRenovacion, TasaInteresRenovacion, 
                    PlazoRenovacion, TasaPeriodo, FechaVencimientoRenovacion, TotalPagarRenovacion, Comprobante
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                id_deposito, id_banco, id_beneficiario, fecha_emision, fecha_vencimiento, moneda, monto, tipo,
                interes_ganado, tasa_interes, 
                capital_renovacion, fecha_emision_renovacion, tasa_interes_renovacion,
                plazo_renovacion, tasa_periodo, fecha_vencimiento_renovacion, total_pagar_renovacion,
                comprobante
            ))

            conn.commit()
            flash("Depósito guardado exitosamente.", "success")

        except Exception as e:
            conn.rollback()
            flash(f"Error al guardar el depósito: {e}", "error")
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('deposito_a_plazo.deposito_a_plazo'))

    # Obtener listado de bancos para el select
    try:
        cursor.execute("SELECT ID_Entidad, Nombre FROM Entidad WHERE TipoEntidad = 'Banco'")
        bancos = cursor.fetchall()
    except Exception as e:
        bancos = []
        flash(f"Error al cargar bancos: {e}", "error")

    cursor.close()
    conn.close()

    # Renderizar el formulario con la lista de bancos
    return render_template('depositos/add_deposito.html', bancos=bancos)






@deposito_a_plazo_bp.route('/edit_deposito/<int:id_deposito>', methods=['GET', 'POST'])
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
                    comprobante = os.path.join(current_app.config['UPLOAD_FOLDER'], filename).replace("\\", "/")
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

        return redirect(url_for('deposito_a_plazo.deposito_a_plazo'))

    # Cargar datos existentes para el formulario
    cursor.execute("SELECT * FROM DepositoAPlazo WHERE ID_Deposito = %s", (id_deposito,))
    deposito = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('depositos/edit_deposito.html', deposito=deposito)

@deposito_a_plazo_bp.route('/delete_deposito/<int:id_deposito>', methods=['POST'])
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

    return redirect(url_for('deposito_a_plazo.deposito_a_plazo'))


@deposito_a_plazo_bp.route('/beneficiarios_por_tipo/<tipo>', methods=['GET'])
@login_required
def beneficiarios_por_tipo(tipo):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if tipo == 'empresa':
            cursor.execute("SELECT ID_Entidad, Nombre, Rut FROM EntidadComercial WHERE TipoEntidad = 'Empresa'")
        elif tipo == 'cliente':
            cursor.execute("SELECT ID_Entidad, Nombre, Rut FROM EntidadComercial WHERE TipoEntidad = 'Cliente'")
        else:
            return jsonify([]), 400  # Tipo inválido

        beneficiarios = [{'id': row[0], 'nombre': row[1], 'rut': row[2]} for row in cursor.fetchall()]
        print(f"Beneficiarios ({tipo}): {beneficiarios}")  # Debug
        return jsonify(beneficiarios)

    except Exception as e:
        print(f"Error al obtener beneficiarios: {e}")
        return jsonify([]), 500
    finally:
        cursor.close()
        conn.close()

@deposito_a_plazo_bp.route('/agregar_beneficiario', methods=['POST'])
@login_required
def agregar_beneficiario():
    try:
        # Obtener datos del JSON enviado
        data = request.json
        rut = data['rut']
        nombre = data['nombre']
        tipo_beneficiario = data['tipo_beneficiario']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insertar el beneficiario según el tipo
        if tipo_beneficiario in ["Empresa", "Cliente"]:
            cursor.execute("""
                INSERT INTO EntidadComercial (Rut, Nombre, TipoEntidad) 
                VALUES (%s, %s, %s) RETURNING ID_Entidad
            """, (rut, nombre, tipo_beneficiario))
        else:
            return jsonify({"success": False, "error": "Tipo de beneficiario inválido"}), 400

        beneficiario_id = cursor.fetchone()[0]
        conn.commit()

        return jsonify({"success": True, "id": beneficiario_id})
    except Exception as e:
        print(f"Error al agregar beneficiario: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@deposito_a_plazo_bp.route('/agregar_banco', methods=['POST'])
@login_required
def agregar_banco():
    try:
        # Obtener datos del JSON enviado
        data = request.json
        rut = data['rut']
        nombre = data['nombre']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insertar banco en la tabla `Entidad`
        cursor.execute("""
            INSERT INTO Entidad (Rut, Nombre, TipoEntidad) 
            VALUES (%s, %s, 'Banco') RETURNING ID_Entidad
        """, (rut, nombre))
        banco_id = cursor.fetchone()[0]
        conn.commit()

        return jsonify({"success": True, "id": banco_id})
    except Exception as e:
        print(f"Error al agregar banco: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

