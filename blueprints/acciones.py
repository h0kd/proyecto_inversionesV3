from flask import Blueprint, render_template, request, flash, url_for, redirect
from flask_login import login_required
from database import get_db_connection
import pandas as pd
import plotly.express as px
import plotly.io as pio

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
        SELECT 
            f.NumeroFactura AS FacturaID,
            a.Ticker AS Ticker,
            f.Fecha AS FechaCompra,
            f.Cantidad AS CantidadAcciones,
            ROUND(f.PrecioUnitario, 2) AS PrecioCompra,
            ROUND(f.Valor, 2) AS ValorTotal,
            ROUND(f.Comision, 2) AS Comision,
            ROUND((
                SELECT 
                    SUM(f_interno.Cantidad * f_interno.PrecioUnitario) / SUM(f_interno.Cantidad)
                FROM Facturas f_interno
                WHERE f_interno.id_accion = a.id
            ), 2) AS PrecioPromedioCompra,
            COALESCE((
                SELECT 
                    SUM(d.valortotal)
                FROM Dividendos d
                WHERE d.id_accion = a.id
            ), 0) AS DividendosTotales,
            f.Tipo AS Tipo
        FROM Facturas f
        JOIN Acciones a ON f.id_accion = a.id
        WHERE a.Empresa = %s
        ORDER BY f.Fecha;
    """

    grafico_query = """
        SELECT
            f.NombreActivo AS Ticker,
            SUM(f.Valor) AS TotalInvertido
        FROM Facturas f
        JOIN EntidadComercial e ON f.ID_Entidad_Comercial = e.ID_Entidad
        WHERE e.Nombre = %s 
        GROUP BY f.NombreActivo
        ORDER BY TotalInvertido DESC;
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
        # Obtener los datos del formulario
        fechacierre = request.form['fecha_cierre']
        fechapago = request.form['fecha_pago']
        valorporaccion = float(request.form['valor_por_accion'])
        moneda = request.form['moneda']

        # El nombre del dividendo será el Ticker
        nombre_dividendo = ticker

        # Conectar a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Obtener la cantidad total de acciones asociadas al Ticker
            cursor.execute("""
                SELECT SUM(f.Cantidad) 
                FROM Facturas f
                JOIN Acciones a ON a.id = f.id_accion
                WHERE a.ticker = %s
            """, (ticker,))
            cantidad_total_acciones = cursor.fetchone()[0]

            # Si no hay acciones, establecer la cantidad como 0
            if not cantidad_total_acciones:
                cantidad_total_acciones = 0

            print(f"Cantidad total de acciones para {ticker}: {cantidad_total_acciones}")  # Depuración

            # Calcular el valor total del dividendo
            valortotal = valorporaccion * cantidad_total_acciones
            print(f"Valor total calculado para el dividendo: {valortotal}")  # Depuración

            # Insertar el dividendo en la base de datos
            cursor.execute("""
                INSERT INTO Dividendos (id_accion, nombre, fechacierre, fechapago, valorporaccion, moneda, valortotal)
                VALUES (
                    (SELECT id FROM Acciones WHERE ticker = %s LIMIT 1),
                    %s, %s, %s, %s, %s, %s
                )
            """, (ticker, nombre_dividendo, fechacierre, fechapago, valorporaccion, moneda, valortotal))
            conn.commit()
            flash(f"Dividendo agregado para {ticker} con éxito.", "success")
        except Exception as e:
            conn.rollback()
            print(f"Error al agregar dividendo: {e}")  # Depuración
            flash(f"Error al agregar dividendo: {e}", "error")
        finally:
            cursor.close()
            conn.close()

        # Redirigir a la vista de detalle de la empresa
        return redirect(url_for('acciones.detalle_empresa', nombre_empresa=nombre_empresa))

    # Renderizar la plantilla para agregar dividendos
    return render_template('acciones/dividendos/add_dividendo.html', ticker=ticker, nombre_empresa=nombre_empresa)





