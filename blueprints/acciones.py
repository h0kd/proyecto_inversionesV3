from flask import Blueprint, render_template, request, flash, url_for, redirect, jsonify
from flask_login import login_required # type: ignore
from database import get_db_connection
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
            # Obtener todas las facturas asociadas al ticker
            cursor.execute("""
                SELECT id_accion, NumeroFactura, Cantidad
                FROM Facturas
                WHERE id_accion IN (
                    SELECT id FROM Acciones WHERE Ticker = %s
                )
            """, (ticker,))
            facturas = cursor.fetchall()

            if not facturas:
                flash("No se encontraron facturas asociadas a este ticker.", "error")
                return redirect(url_for('acciones.acciones_por_ticker', nombre_empresa=nombre_empresa, ticker=ticker))

            for id_accion, numero_factura, cantidad_total_acciones in facturas:
                valortotal = valorporaccion * cantidad_total_acciones

                # Insertar el dividendo para cada factura
                cursor.execute("""
                    INSERT INTO Dividendos (id_accion, id_factura, nombre, fechacierre, fechapago, valorporaccion, moneda, valortotal)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (id_accion, numero_factura, ticker, fechacierre, fechapago, valorporaccion, moneda, valortotal))

            conn.commit()
            flash(f"Dividendos agregados para todas las acciones del ticker {ticker}.", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Error al agregar dividendos: {e}", "error")
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('acciones.acciones_por_ticker', nombre_empresa=nombre_empresa, ticker=ticker))

    return render_template(
        'acciones/dividendos/add_dividendo.html',
        ticker=ticker,
        nombre_empresa=nombre_empresa
    )


@acciones_bp.route('/historial_dividendos/<ticker>/<nombre_empresa>/<numero_factura>', methods=['GET'])
@login_required
def historial_dividendos(ticker, nombre_empresa, numero_factura):
    conn = get_db_connection()
    cursor = conn.cursor()

    dividendos = []
    try:
        # Consulta para obtener los dividendos con rentabilidad
        query = """
            SELECT 
                d.id_dividendo,  -- Incluir el ID del dividendo
                d.fechacierre, 
                d.fechapago, 
                d.valorporaccion, 
                d.moneda, 
                d.valortotal,
                d.rentabilidad
            FROM Dividendos d
            WHERE d.id_factura = %s
        """
        cursor.execute(query, (numero_factura,))
        dividendos = cursor.fetchall()
    except Exception as e:
        print(f"Error al obtener historial de dividendos: {e}")
        flash(f"Error al obtener historial de dividendos: {e}", "error")
    finally:
        cursor.close()
        conn.close()

    return render_template(
        'acciones/dividendos/historial_dividendos.html',
        ticker=ticker,
        nombre_empresa=nombre_empresa,
        numero_factura=numero_factura,
        dividendos=dividendos
    )

@acciones_bp.route('/editar_dividendo/<int:id_dividendo>', methods=['GET'])
@login_required
def editar_dividendo(id_dividendo):
    conn = get_db_connection()
    cursor = conn.cursor()

    dividendo = None
    try:
        query = """
            SELECT id_dividendo, fechacierre, fechapago, valorporaccion, moneda
            FROM Dividendos
            WHERE id_dividendo = %s
        """
        cursor.execute(query, (id_dividendo,))
        dividendo = cursor.fetchone()

        if dividendo:
            # Convertir las fechas a formato YYYY-MM-DD
            fechacierre = datetime.strptime(dividendo[1], "%a, %d %b %Y %H:%M:%S %Z").strftime("%Y-%m-%d")
            fechapago = datetime.strptime(dividendo[2], "%a, %d %b %Y %H:%M:%S %Z").strftime("%Y-%m-%d")
            dividendo = (dividendo[0], fechacierre, fechapago, dividendo[3], dividendo[4])

        if not dividendo:
            flash("El dividendo no existe.", "warning")
            return redirect(url_for('acciones.historial_dividendos'))

    except Exception as e:
        print(f"Error al obtener el dividendo: {e}")
        flash(f"Error al obtener el dividendo: {e}", "error")
    finally:
        cursor.close()
        conn.close()

    return render_template('acciones/dividendos/edit_dividendo.html', dividendo=dividendo)



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
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Obtener los datos enviados desde el formulario
        fecha_cierre = request.form['fecha_cierre']
        fecha_pago = request.form['fecha_pago']
        valor_por_accion = float(request.form['valor_por_accion'])
        moneda = request.form['moneda']

        # Actualizar el dividendo en la base de datos
        cursor.execute("""
            UPDATE Dividendos
            SET fechacierre = %s,
                fechapago = %s,
                valorporaccion = %s,
                moneda = %s,
                valortotal = valorporaccion * (
                    SELECT Cantidad
                    FROM Facturas
                    WHERE id_factura = Dividendos.id_factura
                )
            WHERE id_dividendo = %s
        """, (fecha_cierre, fecha_pago, valor_por_accion, moneda, id_dividendo))

        conn.commit()
        flash("Dividendo actualizado correctamente.", "success")

    except Exception as e:
        conn.rollback()
        flash(f"Error al actualizar el dividendo: {e}", "error")

    finally:
        cursor.close()
        conn.close()

    # Redirigir al historial de dividendos
    return redirect(url_for('acciones.historial_dividendos', ticker=request.form['ticker'], nombre_empresa=request.form['nombre_empresa'], numero_factura=request.form['numero_factura']))



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
