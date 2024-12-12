from flask import Blueprint, render_template, request, flash
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
            SUM(f.Valor) AS TotalDinero
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
        WHERE e.TipoEntidad = 'Empresa'
        GROUP BY e.Nombre
        ORDER BY e.Nombre;
    """

    try: 
        cursor.execute(acciones_query)
        acciones = cursor.fetchall()

        cursor.execute(total_query)
        total_dinero = cursor.fetchone()[0] or 0

        cursor.execute(grafico_query)
        grafico_datos = cursor.fetchall()
    except Exception as e:
        print(f"Error en las consultas: {e}")
        flash(f"Error al obtener las acciones: {e}", "error")
        acciones = []
        total_dinero = 0
        grafico_datos = []

    # Agregar índices
    acciones_con_indices = [(idx + 1, *accion) for idx, accion in enumerate(acciones)]

    cursor.close()
    conn.close()

    labels = [dato[0] for dato in grafico_datos]
    data = [dato[1] for dato in grafico_datos]

    return render_template('acciones/acciones.html', acciones=acciones_con_indices, total_dinero=total_dinero, labels=labels, data=data)


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
        f.NombreActivo AS Ticker,
        f.Fecha AS FechaCompra,
        f.Cantidad AS CantidadAcciones,
        f.PrecioUnitario AS PrecioCompra,
        f.Valor AS ValorTotal,
        f.Comision AS Comision,
        ROUND((
            SELECT 
                SUM(f_interno.Valor) / SUM(f_interno.Cantidad)
            FROM Facturas f_interno
            JOIN EntidadComercial e_interno ON f_interno.ID_Entidad_Comercial = e_interno.ID_Entidad
            WHERE 
                f_interno.NombreActivo = f.NombreActivo
                AND e_interno.Nombre = e.Nombre
        ), 2) AS PrecioPromedioCompra,
        COALESCE(ROUND((
            SELECT 
                SUM(d.valortotal)
            FROM Dividendos d
            WHERE d.id_accion = CAST(f.NombreActivo AS INTEGER)
        ), 2), 0) AS DividendosTotales
    FROM Facturas f
    JOIN EntidadComercial e ON f.ID_Entidad_Comercial = e.ID_Entidad
    WHERE e.Nombre = 'INNOVACIÓN EMPRESARIAL LTDA.'
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
    
    acciones_empresa = []
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


