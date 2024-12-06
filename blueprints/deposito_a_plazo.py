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
                    comprobante_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
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

        return redirect(url_for('deposito_a_plazo'))

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

    return redirect(url_for('deposito_a_plazo'))