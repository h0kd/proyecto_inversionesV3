from flask import Blueprint, render_template, request
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
    query = """
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
    cursor.execute(query)
    acciones = cursor.fetchall()

    # Agregar índices
    acciones_con_indices = [(idx + 1, *accion) for idx, accion in enumerate(acciones)]

    cursor.close()
    conn.close()

    return render_template('acciones/acciones.html', acciones=acciones_con_indices)