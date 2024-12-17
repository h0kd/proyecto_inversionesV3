from flask import Blueprint, render_template, request, flash, url_for, redirect, jsonify, send_file
from flask_login import login_required # type: ignore
from database import get_db_connection
from decimal import Decimal
import pandas as pd
import plotly.express as px
import plotly.io as pio
import datetime


acciones_bp = Blueprint('acciones', __name__)  # Crea el Blueprint

@acciones_bp.route('/acciones', methods=['GET'])
@login_required
def acciones():
    # Conectar a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()

    # Consulta SQL
    acciones_query = """
        SELECT 
        e.Nombre AS NombreEntidad,
        e.Rut AS RutEntidad,
        SUM(f.Cantidad) AS CantidadTotal
        FROM Facturas f
        JOIN EntidadComercial e ON f.ID_Entidad_Comercial = e.ID_Entidad
        WHERE e.TipoEntidad = 'Empresa'
        GROUP BY e.Nombre, e.Rut
        ORDER BY e.Nombre;
    """

    # Consulta para calcular el total en dinero de todas las compras
    total_query = """
        SELECT 
            SUM(CASE WHEN f.Tipo = 'Compra' THEN f.Valor ELSE 0 END) AS TotalCompras,
            SUM(CASE WHEN f.Tipo = 'Venta' THEN f.Valor ELSE 0 END) AS TotalVentas
        FROM Facturas f
        JOIN EntidadComercial e ON f.ID_Entidad_Comercial = e.ID_Entidad
        WHERE e.TipoEntidad = 'Empresa';
    """


    # Grafico
    grafico_query = """
        SELECT 
            e.Nombre AS NombreENtidad,
            SUM(f.valor) as ValorTotal
        FROM Facturas f
        JOIN EntidadComercial e ON f.ID_Entidad_Comercial = e.ID_Entidad
        WHERE e.TipoEntidad = 'Empresa' AND f.Tipo = 'Compra'
        GROUP BY e.Nombre
        ORDER BY e.Nombre;
    """

    try: 
        cursor.execute(acciones_query)
        acciones = cursor.fetchall()

        cursor.execute(total_query)
        totals = cursor.fetchone()
        total_compras = totals[0] or 0
        total_ventas = totals[1] or 0

        cursor.execute(grafico_query)
        grafico_datos = cursor.fetchall()
    except Exception as e:
        print(f"Error en las consultas: {e}")
        flash(f"Error al obtener las acciones: {e}", "error")
        acciones = []
        total_compras = 0
        total_ventas = 0
        grafico_datos = []

    # Agregar índices
    acciones_con_indices = [(idx + 1, *accion) for idx, accion in enumerate(acciones)]

    cursor.close()
    conn.close()

    labels = [dato[0] for dato in grafico_datos]
    data = [dato[1] for dato in grafico_datos]

    return render_template('acciones/acciones.html', acciones=acciones_con_indices, total_ventas=total_ventas, total_compras=total_compras, labels=labels, data=data)


def format_rut(rut):
    # Convertir el RUT a string, quitar puntos y guión si existen
    rut = str(rut).replace(".", "").replace("-", "")

    if len(rut) < 2:  # Validar que el RUT tiene al menos dos caracteres
        return rut

    # Formatear: separar el dígito verificador (último dígito)
    cuerpo = rut[:-1]
    dv = rut[-1]

    # Agregar puntos cada tres dígitos, desde el final
    cuerpo_formateado = "{:,}".format(int(cuerpo)).replace(",", ".")

    # Retornar el RUT en el formato esperado
    return f"{cuerpo_formateado}-{dv}"

@acciones_bp.app_template_filter('format_rut')
def format_rut_filter(rut):
    return format_rut(rut)


@acciones_bp.route('/empresa/<nombre_empresa>', methods=['GET'])
@login_required
def detalle_empresa(nombre_empresa):
    # Conectar a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()

    # Consulta para obtener las acciones relacionadas con la empresa seleccionada y el promedio ponderado
    acciones_query = """
        WITH DividendosTotales AS (
            SELECT 
                f.id_accion,
                SUM(d.valortotal) AS TotalDividendos
            FROM Dividendos d
            JOIN Facturas f ON d.id_accion = f.id_accion
            GROUP BY f.id_accion
        )
        SELECT 
            a.Ticker AS Ticker,
            SUM(CASE 
                WHEN f.Tipo = 'Compra' THEN f.Cantidad 
                WHEN f.Tipo = 'Venta' THEN -f.Cantidad 
                ELSE 0 
            END) AS CantidadTotal,
            SUM(f.Comision) AS ComisionTotal,
            SUM(f.Gasto) AS GastoTotal,
            ROUND(SUM(f.Valor) / NULLIF(SUM(f.Cantidad), 0), 2) AS PromedioCompra,
            SUM(CASE 
                WHEN f.Tipo = 'Compra' THEN f.Valor 
                WHEN f.Tipo = 'Venta' THEN -f.Valor 
                ELSE 0 
            END) AS ValorTotal,
            COALESCE(dt.TotalDividendos, 0) AS DividendosTotales,
            MIN(f.NumeroFactura) AS NumeroFactura -- Incluye numero_factura
        FROM Facturas f
        JOIN Acciones a ON f.id_accion = a.id
        LEFT JOIN DividendosTotales dt ON f.id_accion = dt.id_accion
        WHERE a.Empresa = %s
        GROUP BY a.Ticker, dt.TotalDividendos
        ORDER BY a.Ticker;
    """


    grafico_query = """
        SELECT
            f.NombreActivo AS Ticker,
            SUM(
                CASE 
                    WHEN f.Tipo = 'Compra' THEN f.Valor  -- Sumar las compras
                    WHEN f.Tipo = 'Venta' THEN -f.Valor  -- Restar las ventas
                    ELSE 0
                END
            ) AS TotalNeto
        FROM Facturas f
        JOIN EntidadComercial e ON f.ID_Entidad_Comercial = e.ID_Entidad
        WHERE e.Nombre = %s 
        GROUP BY f.NombreActivo
        ORDER BY TotalNeto DESC;
    """

    promedio_query = """
        SELECT 
            f.NombreActivo AS Ticker,
            SUM(f.Valor) / SUM(f.Cantidad) AS PromedioCompra
        FROM Facturas f
        JOIN EntidadComercial e ON f.ID_Entidad_Comercial = e.ID_Entidad
        WHERE e.Nombre = %s
        GROUP BY f.NombreActivo
        ORDER BY Ticker;
    """
    

    grafico_data = []
    promedio_data = []
    acciones_empresa = []
    labels = []
    data = []
    promedio_labels = []
    grafico_labels = []
    grafico_data_values = []

    try:
        cursor.execute(acciones_query, (nombre_empresa,))
        acciones_empresa = cursor.fetchall()

        cursor.execute(grafico_query, (nombre_empresa,))
        grafico_data = cursor.fetchall()

        cursor.execute(promedio_query, (nombre_empresa,))
        promedio_data = cursor.fetchall()

        labels = [accion[0] for accion in acciones_empresa]
        data = [accion[4] for accion in acciones_empresa]

        grafico_labels = [row[0] for row in grafico_data]
        grafico_data_values = [row[1] for row in grafico_data]

        promedio_labels = [promedio[0] for promedio in promedio_data]
        promedio_data = [promedio[1] for promedio in promedio_data]
    except Exception as e:
        print(f"Error al obtener las acciones de la empresa '{nombre_empresa}': {e}")
        flash(f"Error al obtener las acciones de la empresa '{nombre_empresa}'.", "error")
        
    finally:
        cursor.close()
        conn.close()

    return render_template(
        'acciones/acciones_empresas.html',
        nombre_empresa=nombre_empresa,
        acciones_empresa=acciones_empresa, labels=labels, data=data, grafico_labels=grafico_labels, grafico_data_values=grafico_data_values, promedio_labels=promedio_labels, promedio_data=promedio_data
    )

@acciones_bp.route('/acciones_por_ticker/<nombre_empresa>/<ticker>', methods=['GET'])
@login_required
def acciones_por_ticker(nombre_empresa, ticker):
    # Conectar a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()

    acciones = []
    try:
        print(f"Nombre empresa: {nombre_empresa}, Ticker: {ticker}")  # Depuración

        # Consulta SQL ajustada para mostrar compras y ventas
        query = """
        SELECT 
            f.NumeroFactura, 
            f.Tipo AS Tipo,  -- Compra o Venta
            f.Fecha AS FechaTransaccion, 
            f.Cantidad AS CantidadAcciones, 
            ROUND(f.PrecioUnitario, 2) AS PrecioTransaccion, 
            ROUND(f.Comision, 2) AS Comision,
            f.Gasto AS Gastos, 
            ROUND((SELECT 
                        SUM(f_interno.Valor) / SUM(f_interno.Cantidad)
                   FROM Facturas f_interno
                   JOIN Acciones a_interno ON a_interno.id = f_interno.id_accion
                   WHERE a_interno.Ticker = %s 
                   AND a_interno.Empresa = %s
                  ), 2) AS PrecioPromedioCompra,
            ROUND(f.Valor, 2) AS ValorTotal,
            f.AdjuntoFactura AS PDF
        FROM Facturas f
        JOIN Acciones a ON a.id = f.id_accion
        WHERE a.Empresa = %s AND a.Ticker = %s
        ORDER BY f.Fecha;
        """
        cursor.execute(query, (ticker, nombre_empresa, nombre_empresa, ticker))
        acciones = cursor.fetchall()
        print(f"Resultados de la consulta: {acciones}")  # Depuración
    except Exception as e:
        flash(f"Error al obtener acciones para el ticker {ticker}: {e}", "error")
        print(f"Error al ejecutar la consulta: {e}")  # Depuración
    finally:
        cursor.close()
        conn.close()

    return render_template(
        'acciones/acciones_por_ticker.html',
        nombre_empresa=nombre_empresa,
        ticker=ticker,
        acciones=acciones
    )




@acciones_bp.route('/add_dividendo/<ticker>/<nombre_empresa>', methods=['GET', 'POST'])
@login_required
def add_dividendo(ticker, nombre_empresa):
    if request.method == 'POST':
        fechacierre = request.form['fecha_cierre']
        fechapago = request.form['fecha_pago']
        valorporaccion = float(request.form['valor_por_accion'])
        moneda = request.form['moneda']

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Obtener todas las acciones asociadas al ticker y la empresa
            cursor.execute("""
                SELECT a.id, SUM(f.Cantidad) AS CantidadTotal
                FROM Acciones a
                JOIN Facturas f ON f.id_accion = a.id
                WHERE a.Ticker = %s AND a.Empresa = %s
                GROUP BY a.id
            """, (ticker, nombre_empresa))
            acciones = cursor.fetchall()

            if not acciones:
                flash("No se encontraron acciones asociadas a este ticker y empresa.", "error")
                return redirect(url_for('acciones.detalle_empresa', nombre_empresa=nombre_empresa))

            # Agregar el dividendo para cada id_accion
            for id_accion, cantidad_total in acciones:
                valortotal = valorporaccion * cantidad_total

                cursor.execute("""
                    INSERT INTO Dividendos (id_accion, nombre, fechacierre, fechapago, valorporaccion, moneda, valortotal)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (id_accion, ticker, fechacierre, fechapago, valorporaccion, moneda, valortotal))

            conn.commit()
            flash(f"Dividendos agregados exitosamente para todas las acciones de {ticker}.", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Error al agregar dividendos: {e}", "error")
        finally:
            cursor.close()
            conn.close()

        # Redirigir al historial de dividendos (no atado a una factura)
        return redirect(url_for('acciones.historial_dividendos', ticker=ticker, nombre_empresa=nombre_empresa, numero_factura=0))

    return render_template(
        'acciones/dividendos/add_dividendo.html',
        ticker=ticker,
        nombre_empresa=nombre_empresa
    )



@acciones_bp.route('/historial_dividendos/<ticker>/<nombre_empresa>', methods=['GET'])
@login_required
def historial_dividendos(ticker, nombre_empresa):
    conn = get_db_connection()
    cursor = conn.cursor()

    dividendos = []
    try:
        # Obtener dividendos para todas las acciones del ticker y empresa
        query = """
            SELECT 
                d.id_dividendo,       -- Aseguramos que sea el primer campo
                d.fechacierre, 
                d.fechapago, 
                d.valorporaccion, 
                d.moneda, 
                d.valortotal,
                d.rentabilidad
            FROM Dividendos d
            JOIN Acciones a ON d.id_accion = a.id
            WHERE a.Ticker = %s AND a.Empresa = %s
        """

        cursor.execute(query, (ticker, nombre_empresa))
        dividendos = cursor.fetchall()
    except Exception as e:
        flash(f"Error al obtener el historial de dividendos: {e}", "error")
    finally:
        cursor.close()
        conn.close()

    return render_template(
        'acciones/dividendos/historial_dividendos.html',
        ticker=ticker,
        nombre_empresa=nombre_empresa,
        dividendos=dividendos
    )

@acciones_bp.route('/editar_dividendo/<int:id_dividendo>', methods=['GET'])
@login_required
def editar_dividendo(id_dividendo):
    conn = get_db_connection()
    cursor = conn.cursor()

    dividendo = None
    ticker = None
    nombre_empresa = "INNOVACIÓN EMPRESARIAL LTDA."  # Ajusta esto si quieres obtenerlo dinámicamente
    numero_factura = None

    try:
        query = """
            SELECT id_dividendo, fechacierre, fechapago, valorporaccion, moneda, nombre, id_factura
            FROM Dividendos
            WHERE id_dividendo = %s
        """
        cursor.execute(query, (id_dividendo,))
        dividendo = cursor.fetchone()

        if dividendo:
            # Extraer los datos necesarios
            fechacierre = dividendo[1].strftime("%Y-%m-%d") if dividendo[1] else None
            fechapago = dividendo[2].strftime("%Y-%m-%d") if dividendo[2] else None
            ticker = dividendo[5]
            numero_factura = dividendo[6]
            # Convertir dividendo a una estructura amigable para la plantilla
            dividendo = (dividendo[0], fechacierre, fechapago, dividendo[3], dividendo[4])

        if not dividendo:
            flash("El dividendo no existe.", "warning")
            return redirect(url_for('acciones.historial_dividendos', ticker=ticker or '', nombre_empresa=nombre_empresa, numero_factura=numero_factura or ''))

    except Exception as e:
        flash(f"Error al obtener el dividendo: {e}", "error")
        return redirect(url_for('acciones.historial_dividendos', ticker=ticker or '', nombre_empresa=nombre_empresa, numero_factura=numero_factura or ''))
    finally:
        cursor.close()
        conn.close()

    return render_template(
        'acciones/dividendos/edit_dividendo.html',
        dividendo=dividendo,
        ticker=ticker,
        nombre_empresa=nombre_empresa,
        numero_factura=numero_factura
    )



@acciones_bp.route('/eliminar_dividendo/<int:id_dividendo>', methods=['POST'])
@login_required
def eliminar_dividendo(id_dividendo):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Depuración: imprime el ID recibido
        print(f"Intentando eliminar dividendo con ID: {id_dividendo}")
        cursor.execute("DELETE FROM Dividendos WHERE id_dividendo = %s", (id_dividendo,))
        conn.commit()
        flash("Dividendo eliminado exitosamente.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al eliminar el dividendo: {e}", "error")
    finally:
        cursor.close()
        conn.close()

    # Redirige al historial de dividendos o página previa
    return redirect(request.referrer or url_for('acciones.historial_dividendos'))



@acciones_bp.route('/actualizar_dividendo/<int:id_dividendo>', methods=['POST'])
@login_required
def actualizar_dividendo(id_dividendo):
    # Obtener valores del formulario
    fechacierre = request.form['fecha_cierre']
    fechapago = request.form['fecha_pago']
    valorporaccion = float(request.form['valor_por_accion'])
    moneda = request.form['moneda']
    ticker = request.form['ticker']
    nombre_empresa = request.form['nombre_empresa']
    numero_factura = request.form.get('numero_factura')  # Obtener de forma segura

    print("Valores recibidos del formulario:")
    print("fechacierre:", fechacierre)
    print("fechapago:", fechapago)
    print("valorporaccion:", valorporaccion)
    print("moneda:", moneda)
    print("ticker:", ticker)
    print("nombre_empresa:", nombre_empresa)
    print("numero_factura:", numero_factura)

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Obtener cantidad total de acciones asociadas
        cursor.execute("""
            SELECT SUM(Cantidad) 
            FROM Facturas f
            JOIN Dividendos d ON f.id_accion = d.id_accion
            WHERE d.id_dividendo = %s
        """, (id_dividendo,))
        resultado = cursor.fetchone()
        cantidad_total_acciones = float(resultado[0] or 0)  # Convertir a float

        print("Cantidad total de acciones asociadas:", cantidad_total_acciones)

        # Calcular valor total
        valortotal = valorporaccion * cantidad_total_acciones
        print("Valor total recalculado:", valortotal)

        # Obtener el valor neto de la acción
        cursor.execute("""
            SELECT SUM(CASE 
                        WHEN f.Tipo = 'Compra' THEN f.Cantidad * f.PrecioUnitario + COALESCE(f.Comision, 0)
                        WHEN f.Tipo = 'Venta' THEN -(f.Cantidad * f.PrecioUnitario + COALESCE(f.Comision, 0))
                      END) AS ValorNeto
            FROM Facturas f
            JOIN Dividendos d ON f.id_accion = d.id_accion
            WHERE d.id_dividendo = %s
        """, (id_dividendo,))
        valor_neto = float(cursor.fetchone()[0] or 1)  # Convertir a float y evitar división por 0

        print("Valor neto calculado:", valor_neto)

        # Calcular rentabilidad
        rentabilidad = round((valortotal / valor_neto) * 100, 2)
        print("Rentabilidad calculada:", rentabilidad)

        # Actualizar el dividendo
        cursor.execute("""
            UPDATE Dividendos
            SET fechacierre = %s, 
                fechapago = %s, 
                valorporaccion = %s, 
                moneda = %s, 
                valortotal = %s,
                rentabilidad = %s
            WHERE id_dividendo = %s
        """, (fechacierre, fechapago, valorporaccion, moneda, valortotal, rentabilidad, id_dividendo))

        conn.commit()
        print("Dividendo actualizado correctamente en la base de datos.")
        flash("Dividendo actualizado exitosamente con nuevos cálculos.", "success")

    except Exception as e:
        conn.rollback()
        print(f"Error al actualizar el dividendo: {e}")
        flash(f"Error al actualizar el dividendo: {e}", "error")
    finally:
        cursor.close()
        conn.close()

    # Redirección corregida
    print("Redireccionando al historial de dividendos...")
    return redirect(url_for('acciones.historial_dividendos', ticker=ticker, nombre_empresa=nombre_empresa, numero_factura=numero_factura))



@acciones_bp.route('/debug_dividendo/<int:id_dividendo>', methods=['GET'])
def debug_dividendo(id_dividendo):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = """
            SELECT id_dividendo, fechacierre, fechapago, valorporaccion, moneda
            FROM Dividendos
            WHERE id_dividendo = %s
        """
        cursor.execute(query, (id_dividendo,))
        dividendo = cursor.fetchone()
        return jsonify(dividendo)  # Devuelve los datos en formato JSON
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        cursor.close()
        conn.close()

@acciones_bp.route('/acciones_por_corredora/<nombre_empresa>', methods=['GET', 'POST'])
@login_required
def acciones_por_corredora(nombre_empresa):
    conn = get_db_connection()
    cursor = conn.cursor()

    corredoras = []
    acciones = []
    resultados = []
    totales = {
        "cantidad_total": 0,
        "comision_total": 0,
        "gasto_total": 0,
        "valor_total": 0
    }

    try:
        # Obtener corredoras registradas en la tabla Entidad
        cursor.execute("""
            SELECT DISTINCT e.Nombre
            FROM Entidad e
            JOIN Facturas f ON e.id_entidad = f.id_entidad
            JOIN Acciones a ON f.id_accion = a.id
            WHERE a.Empresa = %s AND LOWER(e.tipoentidad) = 'corredor'
        """, (nombre_empresa,))
        corredoras = [row[0] for row in cursor.fetchall()]

        # Obtener acciones disponibles en la empresa
        cursor.execute("""
            SELECT DISTINCT a.Ticker
            FROM Acciones a
            JOIN Facturas f ON a.id = f.id_accion
            WHERE a.Empresa = %s
        """, (nombre_empresa,))
        acciones = [row[0] for row in cursor.fetchall()]

        # Filtrar resultados si se selecciona una corredora y/o acción
        if request.method == 'POST':
            corredora = request.form.get('corredora')
            accion = request.form.get('accion')

            query = """
                SELECT f.NumeroFactura, a.Ticker, f.Cantidad, f.Comision, f.Gasto, 
                       f.PrecioUnitario, f.Valor, f.adjuntofactura, f.Tipo
                FROM Facturas f
                JOIN Acciones a ON f.id_accion = a.id
                JOIN Entidad e ON f.id_entidad = e.id_entidad
                WHERE a.Empresa = %s AND LOWER(e.tipoentidad) = 'corredor'
            """
            params = [nombre_empresa]

            if corredora:
                query += " AND e.Nombre = %s"
                params.append(corredora)
            if accion:
                query += " AND a.Ticker = %s"
                params.append(accion)

            cursor.execute(query, tuple(params))
            resultados = cursor.fetchall()

            # Calcular totales si hay una acción seleccionada
            if accion:
                query_totales = """
                    SELECT SUM(f.Cantidad), SUM(f.Comision), SUM(f.Gasto), SUM(f.Valor)
                    FROM Facturas f
                    JOIN Acciones a ON f.id_accion = a.id
                    JOIN Entidad e ON f.id_entidad = e.id_entidad
                    WHERE a.Empresa = %s AND a.Ticker = %s AND LOWER(e.tipoentidad) = 'corredor'
                """
                params_totales = [nombre_empresa, accion]

                if corredora:  # Filtrar por corredora si está seleccionada
                    query_totales += " AND e.Nombre = %s"
                    params_totales.append(corredora)

                cursor.execute(query_totales, tuple(params_totales))
                total_result = cursor.fetchone()
                if total_result:
                    totales["cantidad_total"] = total_result[0] or 0
                    totales["comision_total"] = float(total_result[1] or 0)
                    totales["gasto_total"] = float(total_result[2] or 0)
                    totales["valor_total"] = float(total_result[3] or 0)


    except Exception as e:
        flash(f"Error al obtener datos: {e}", "error")
    finally:
        cursor.close()
        conn.close()

    return render_template(
        'acciones/acciones_por_corredora.html',
        nombre_empresa=nombre_empresa,
        corredoras=corredoras,
        acciones=acciones,
        resultados=resultados,
        totales=totales
    )



@acciones_bp.route('/descargar_pdf')
@login_required
def descargar_pdf():
    pdf_path = request.args.get('pdf_path')
    return send_file(pdf_path, as_attachment=True)

