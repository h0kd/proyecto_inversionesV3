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
            promedio_compra.PrecioPromedioCompra
        FROM Facturas f
        JOIN EntidadComercial e ON f.ID_Entidad_Comercial = e.ID_Entidad
        LEFT JOIN (
            SELECT 
                NombreActivo, 
                SUM(Valor) / SUM(Cantidad) AS PrecioPromedioCompra
            FROM Facturas
            GROUP BY NombreActivo
        ) AS promedio_compra ON f.NombreActivo = promedio_compra.NombreActivo
        WHERE e.Nombre = %s
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
    
    acciones_empresa = []
    grafico_data = []
    try:
        cursor.execute(acciones_query, (nombre_empresa,))
        acciones_empresa = cursor.fetchall()

        cursor.execute(grafico_query, (nombre_empresa,))
        grafico_data = cursor.fetchall()

        labels = [accion[0] for accion in acciones_empresa]
        data = [accion[4] for accion in acciones_empresa]
    except Exception as e:
        print(f"Error al obtener las acciones de la empresa '{nombre_empresa}': {e}")
        flash(f"Error al obtener las acciones de la empresa '{nombre_empresa}'.", "error")
        acciones_empresa = []
        labels = []
        data = []
    finally:
        cursor.close()
        conn.close()

    grafico_labels = [row[0] for row in grafico_data]
    grafico_data_values = [row[1] for row in grafico_data]

    return render_template(
        'acciones/acciones_empresas.html',
        nombre_empresa=nombre_empresa,
        acciones_empresa=acciones_empresa, labels=labels, data=data, grafico_labels=grafico_labels, grafico_data_values=grafico_data_values
    )


