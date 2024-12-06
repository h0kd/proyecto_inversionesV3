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
                tipo_entidad = request.form['tipo_entidad']
                id_entidad = request.form['nombre_entidad']  # ID de la entidad seleccionada
                nombre_activo = request.form['nombre_activo'].upper()
                fecha = request.form['fecha']
                tipo = request.form['tipo'].capitalize()
                cantidad = float(request.form['cantidad'])
                precio_unitario = float(request.form['precio_unitario'])
                subtotal = cantidad * precio_unitario
                valor_total = float(request.form['valor_total'])
                comision = float(request.form.get('comision', 0))
                gasto = float(request.form.get('gasto', 0))

                # Manejar archivo adjunto
                archivo = request.files['archivo_factura']
                if archivo and allowed_file(archivo.filename):
                    filename = secure_filename(archivo.filename)
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file_path = file_path.replace("\\", "/")
                    archivo.save(file_path)
                    print(f"Archivo guardado en: {file_path}")
                else:
                    flash("Error: Archivo no válido o no seleccionado.", "error")
                    print("Error en el archivo: Archivo no válido o no seleccionado.")
                    return redirect(url_for('add_factura'))

                # Determinar dónde guardar el ID y el valor de `tipo_entidad`
                id_entidad_val = None
                id_entidad_comercial_val = None
                tipo_entidad_factura = None

                if tipo_entidad in ['Banco', 'Compania', 'Corredor']:
                    id_entidad_val = id_entidad
                    tipo_entidad_factura = 'Entidad'
                elif tipo_entidad in ['Cliente', 'Empresa']:
                    id_entidad_comercial_val = id_entidad
                    tipo_entidad_factura = 'EntidadComercial'
                else:
                    flash("Tipo de entidad no válido.", "error")
                    print(f"Error: Tipo de entidad no válido - {tipo_entidad}")
                    return redirect(url_for('add_factura'))

                # Obtener ID de TipoInversion basado en el tipo
                cursor.execute("SELECT ID FROM TipoInversion WHERE Nombre = %s", (tipo,))
                tipo_inversion_result = cursor.fetchone()
                if not tipo_inversion_result:
                    flash(f"Error: Tipo de inversión '{tipo}' no encontrado.", "error")
                    print(f"Error: Tipo de inversión '{tipo}' no encontrado.")
                    return redirect(url_for('add_factura'))

                id_tipo_inversion = tipo_inversion_result[0]

                # Insertar la factura en la base de datos
                print("Intentando insertar la factura en la base de datos.")
                cursor.execute("""
                    INSERT INTO Facturas 
                    (NumeroFactura, ID_Entidad, ID_Entidad_Comercial, Fecha, Tipo, Cantidad, PrecioUnitario, SubTotal, Valor, NombreActivo, Comision, Gasto, AdjuntoFactura, ID_TipoInversion, Tipo_Entidad)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, (
                    numero_factura, id_entidad_val, id_entidad_comercial_val, fecha, tipo, cantidad, precio_unitario,
                    subtotal, valor_total, nombre_activo, comision, gasto, file_path, id_tipo_inversion, tipo_entidad_factura
                ))
                conn.commit()
                print("Factura insertada exitosamente.")

                flash("Factura agregada exitosamente.", "success")
                return redirect(url_for('listado_facturas'))

            except Exception as e:
                conn.rollback()
                print(f"Error al agregar la factura: {e}")
                flash(f"Error al agregar la factura: {e}", "error")
                return redirect(url_for('add_factura'))

        else:
            print("GET recibido: Preparando el formulario para agregar factura.")
            # Obtener las opciones para el select de Tipo de Entidad y Nombre de Entidad
            cursor.execute("SELECT DISTINCT TipoEntidad FROM Entidad")
            tipos_entidad = cursor.fetchall()

            cursor.execute("SELECT ID_Entidad, Nombre FROM Entidad")
            entidades = cursor.fetchall()

            cursor.execute("SELECT ID_Entidad, Nombre FROM EntidadComercial")
            entidades_comerciales = cursor.fetchall()

            return render_template(
                'facturas/add_factura.html',
                tipos_entidad=tipos_entidad,
                entidades=entidades,
                entidades_comerciales=entidades_comerciales
            )
    except Exception as e:
        print(f"Error en la conexión o lógica general: {e}")
        flash(f"Error en la conexión: {e}", "error")
        return redirect(url_for('listado_facturas'))
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
                return redirect(url_for('listado_facturas'))

            except Exception as e:
                conn.rollback()
                flash(f"Error al actualizar la factura: {e}", "error")
                return redirect(url_for('editar_factura', numero_factura=numero_factura))

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
                return redirect(url_for('listado_facturas'))

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

    return redirect(url_for('listado_facturas'))

@facturas_bp.route('/entidades_por_tipo/<tipo>', methods=['GET'])
@login_required
def entidades_por_tipo(tipo):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if tipo in ['Banco', 'Corredor', 'Compania']:
            # Consultar en la tabla Entidad
            cursor.execute("""
                SELECT ID_Entidad, Nombre 
                FROM Entidad 
                WHERE TipoEntidad = %s
            """, (tipo,))
        elif tipo in ['Empresa', 'Cliente']:
            # Consultar en la tabla EntidadComercial
            cursor.execute("""
                SELECT ID_Entidad, Nombre 
                FROM EntidadComercial 
                WHERE TipoEntidad = %s
            """, (tipo,))
        else:
            return jsonify({"error": "Tipo de entidad no válido"}), 400

        entidades = cursor.fetchall()

        # Formatear como JSON
        resultado = [{"id": entidad[0], "nombre": entidad[1]} for entidad in entidades]
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()