from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from database import get_db_connection
from werkzeug.utils import secure_filename
from helpers.utils import allowed_file
from flask import current_app
import os

# Crear el Blueprint
facturas_bp = Blueprint('facturas', __name__)


@facturas_bp.route('/add_factura', methods=['GET', 'POST'])
@login_required
def add_factura():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'POST':
            try:
                # Registra los datos recibidos del formulario
                print("POST recibido: Procesando datos de la factura.")
                print(f"Datos enviados: {request.form}")

                # Recibir datos del formulario
                numero_factura = request.form['numero_factura']
                id_corredora = request.form.get('corredora')  # ID de la corredora seleccionada
                id_empresa_emisora = request.form.get('empresa_emisora')  # ID de la empresa emisora seleccionada
                nombre_activo = request.form['nombre_activo'].upper()
                fecha = request.form['fecha']
                tipo = request.form['tipo'].capitalize()
                cantidad = float(request.form['cantidad'])
                precio_unitario = float(request.form['precio_unitario'])
                subtotal = cantidad * precio_unitario
                valor_total = float(request.form['valor_total'])
                comision = float(request.form.get('comision', 0))
                gasto = float(request.form.get('gasto', 0))

                # Validar que ambos select tengan valores
                if not id_corredora or not id_empresa_emisora:
                    flash("Por favor, seleccione una corredora y una empresa emisora.", "error")
                    print("Error: No se seleccionaron todos los campos requeridos.")
                    return redirect(url_for('facturas.add_factura'))

                # Manejar archivo adjuntofactura
                adjuntofactura = None
                if 'adjuntofactura' in request.files and request.files['adjuntofactura'].filename != '':
                    file = request.files['adjuntofactura']
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        relative_path = os.path.join('static', 'uploads', filename)
                        adjuntofactura_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                        os.makedirs(os.path.dirname(adjuntofactura_path), exist_ok=True)
                        file.save(adjuntofactura_path)
                        adjuntofactura = relative_path

                # Obtener ID de TipoInversion basado en el tipo
                cursor.execute("SELECT ID FROM TipoInversion WHERE Nombre = %s", (tipo,))
                tipo_inversion_result = cursor.fetchone()
                if not tipo_inversion_result:
                    flash(f"Error: Tipo de inversión '{tipo}' no encontrado.", "error")
                    print(f"Error: Tipo de inversión '{tipo}' no encontrado.")
                    return redirect(url_for('facturas.add_factura'))

                id_tipo_inversion = tipo_inversion_result[0]

                # Insertar la factura en la base de datos
                print("Intentando insertar la factura en la base de datos.")
                cursor.execute("""
                    INSERT INTO Facturas 
                    (NumeroFactura, ID_Entidad, ID_Entidad_Comercial, Fecha, Tipo, Cantidad, PrecioUnitario, SubTotal, Valor, NombreActivo, Comision, Gasto, AdjuntoFactura, ID_TipoInversion, Tipo_Entidad)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, (
                    numero_factura, id_corredora, id_empresa_emisora, fecha, tipo, cantidad, precio_unitario,
                    subtotal, valor_total, nombre_activo, comision, gasto, adjuntofactura, id_tipo_inversion, 'EntidadComercial'
                ))
                conn.commit()
                print("Factura insertada exitosamente.")

                flash("Factura agregada exitosamente.", "success")
                return redirect(url_for('facturas.listado_facturas'))

            except Exception as e:
                conn.rollback()
                print(f"Error al agregar la factura: {e}")
                flash(f"Error al agregar la factura: {e}", "error")
                return redirect(url_for('facturas.add_factura'))

        else:
            print("GET recibido: Preparando el formulario para agregar factura.")
            return render_template('facturas/add_factura.html')

    except Exception as e:
        print(f"Error en la conexión o lógica general: {e}")
        flash(f"Error en la conexión: {e}", "error")
        return redirect(url_for('facturas.listado_facturas'))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@facturas_bp.route('/listado_facturas', methods=['GET'])
@login_required
def listado_facturas():
    sort_by = request.args.get('sort_by', 'NumeroFactura')  # Ordenar por NumeroFactura por defecto
    order = request.args.get('order', 'asc')  # Orden ascendente por defecto

    valid_columns = ['NumeroFactura', 'NombreEntidad', 'NombreActivo', 'Tipo', 'Fecha', 'Cantidad', 'PrecioUnitario', 'SubTotal', 'Valor']
    if sort_by not in valid_columns:
        sort_by = 'NumeroFactura'

    if order not in ['asc', 'desc']:
        order = 'asc'

    conn = get_db_connection()
    cursor = conn.cursor()

    query = f"""
        SELECT 
            f.NumeroFactura, 
            CASE 
                WHEN f.tipo_entidad = 'Entidad' THEN e.Nombre
                WHEN f.tipo_entidad = 'EntidadComercial' THEN ec.Nombre
            END AS NombreEntidad, 
            f.NombreActivo, 
            f.Tipo,
            f.Fecha, 
            f.Cantidad, 
            f.PrecioUnitario, 
            f.SubTotal, 
            f.Valor, 
            f.AdjuntoFactura
        FROM Facturas f
        LEFT JOIN Entidad e ON f.ID_Entidad = e.ID_Entidad AND f.tipo_entidad = 'Entidad'
        LEFT JOIN EntidadComercial ec ON f.ID_Entidad_Comercial = ec.ID_Entidad AND f.tipo_entidad = 'EntidadComercial'
        ORDER BY {sort_by} {order};
    """
    try:
        cursor.execute(query)
        facturas = cursor.fetchall()
    except Exception as e:
        print(f"Error en la consulta: {e}")  # Debug
        flash(f"Error al listar las facturas: {e}", "error")
        facturas = []

    cursor.close()
    conn.close()

    return render_template('facturas/listado_facturas.html', facturas=facturas, sort_by=sort_by, order=order)

@facturas_bp.route('/edit_factura/<int:numero_factura>', methods=['GET', 'POST'])
@login_required
def editar_factura(numero_factura):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'POST':
            try:
                # Recibir datos del formulario
                nuevo_numero_factura = request.form['nuevo_numero']
                tipo_entidad = request.form['tipo_entidad']
                id_entidad = request.form['nombre_entidad']  # ID seleccionada
                nombre_activo = request.form['nombre_activo']
                tipo = request.form['tipo']
                fecha = request.form['fecha']
                cantidad = float(request.form['cantidad'])
                precio_unitario = float(request.form['precio_unitario'])
                comision = float(request.form.get('comision', 0))
                gasto = float(request.form.get('gasto', 0))
                subtotal = cantidad * precio_unitario
                valor_total = float(request.form['valor_total'])
                

                # Determinar valores según el tipo de entidad
                tipo_entidad_factura = None
                id_entidad_val = None
                id_entidad_comercial_val = None

                if tipo_entidad in ['Banco', 'Compania', 'Corredor']:
                    tipo_entidad_factura = 'Entidad'
                    id_entidad_val = id_entidad
                elif tipo_entidad in ['Cliente', 'Empresa']:
                    tipo_entidad_factura = 'EntidadComercial'
                    id_entidad_comercial_val = id_entidad

                print(tipo_entidad_factura)
                # Actualizar la factura, incluyendo la columna `tipo_entidad`
                cursor.execute("""
                    UPDATE Facturas
                    SET NumeroFactura = %s, ID_Entidad = %s, ID_Entidad_Comercial = %s, Tipo_Entidad = %s, 
                        NombreActivo = %s, Tipo = %s, Fecha = %s, Cantidad = %s, Comision = %s, Gasto = %s, PrecioUnitario = %s, SubTotal = %s, Valor = %s
                    WHERE NumeroFactura = %s
                """, (
                    nuevo_numero_factura, id_entidad_val, id_entidad_comercial_val, tipo_entidad_factura,
                    nombre_activo, tipo, fecha, cantidad, comision, gasto, precio_unitario, subtotal, valor_total, numero_factura
                ))
                conn.commit()

                flash("Factura actualizada exitosamente.", "success")
                return redirect(url_for('facturas.listado_facturas'))

            except Exception as e:
                conn.rollback()
                flash(f"Error al actualizar la factura: {e}", "error")
                return redirect(url_for('facturas.editar_factura', numero_factura=numero_factura))

        else:
            # Obtener datos de la factura
            cursor.execute("""
                SELECT NumeroFactura, NombreActivo, Tipo, Fecha, Cantidad, Comision, Gasto, Tipo_Entidad, 
                       COALESCE(ID_Entidad, ID_Entidad_Comercial) AS ID_Entidad,
                           PrecioUnitario, Valor, SubTotal
                FROM Facturas 
                WHERE NumeroFactura = %s
            """, (numero_factura,))
            factura = cursor.fetchone()

            if not factura:
                flash("Factura no encontrada.", "error")
                return redirect(url_for('facturas.listado_facturas'))

            # Cargar tipos de entidad
            cursor.execute("""
                SELECT DISTINCT TipoEntidad FROM (
                    SELECT TipoEntidad FROM Entidad
                    UNION ALL
                    SELECT TipoEntidad FROM EntidadComercial
                ) subquery
            """)
            tipos_entidad = [row[0] for row in cursor.fetchall()]

            # Cargar entidades del tipo seleccionado
            cursor.execute("""
                SELECT ID_Entidad, Nombre FROM Entidad WHERE TipoEntidad = %s
                UNION ALL
                SELECT ID_Entidad, Nombre FROM EntidadComercial WHERE TipoEntidad = %s
            """, (factura[7], factura[7]))
            entidades = cursor.fetchall()

            return render_template('facturas/edit_factura.html', factura=factura, tipos_entidad=tipos_entidad, entidades=entidades)

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


@facturas_bp.route('/eliminar_factura/<int:numero_factura>', methods=['POST', 'GET'])
@login_required
def eliminar_factura(numero_factura):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Eliminar la factura
    cursor.execute("DELETE FROM Facturas WHERE NumeroFactura = %s", (numero_factura,))
    conn.commit()
    conn.close()

    return redirect(url_for('facturas.listado_facturas'))

@facturas_bp.route('/entidades_corredor', methods=['GET'])
@login_required
def entidades_corredor():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ID_Entidad, Nombre FROM Entidad WHERE TipoEntidad = 'Corredor'")
        corredores = cursor.fetchall()

        if not corredores:
            print("No se encontraron corredores en la base de datos.")

        resultado = [{"id": corredor[0], "nombre": corredor[1]} for corredor in corredores]
        return jsonify(resultado)
    except Exception as e:
        print(f"Error al obtener corredoras: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()



@facturas_bp.route('/entidades_empresa', methods=['GET'])
@login_required
def entidades_empresa():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ID_Entidad, Nombre FROM EntidadComercial WHERE TipoEntidad = 'Empresa'")
        empresas = cursor.fetchall()

        if not empresas:
            print("No se encontraron empresas emisoras en la base de datos.")

        resultado = [{"id": empresa[0], "nombre": empresa[1]} for empresa in empresas]
        return jsonify(resultado)
    except Exception as e:
        print(f"Error al obtener empresas emisoras: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

