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
    # Obtener parámetros de búsqueda y ordenamiento
    sort_by = request.args.get('sort_by', 'Fecha')          # Ordenar por Fecha por defecto
    order = request.args.get('order', 'asc')                # Orden ascendente por defecto

    # Validar las columnas para evitar SQL injection
    valid_columns = ['NumeroFactura', 'Corredora', 'Fecha', 'Tipo', 'Ticker', 
                 'Cantidad', 'PrecioUnitario', 'Comision', 'CostoTotal', 
                 'PrecioPromedioCompra']

    if sort_by not in valid_columns:
        sort_by = 'Fecha'
    if order not in ['asc', 'desc']:
        order = 'asc'

    # Conectar a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()

    # Construir la consulta SQL con filtros dinámicos
    query = f"""
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

    params = []

    cursor.execute(query, params)
    acciones = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('acciones/acciones.html', acciones=acciones)

@acciones_bp.route('/acciones_rendimiento', methods=['GET'])
@login_required
def acciones_rendimiento():
    # Conectar a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()

    # Consulta para obtener datos necesarios
    cursor.execute("""
        SELECT 
            f.Fecha, 
            f.NombreActivo AS Ticker, 
            f.PrecioUnitario AS Precio, 
            f.Tipo, 
            f.Cantidad
        FROM Facturas f
        WHERE f.Tipo IN ('Compra', 'Venta')
        ORDER BY f.Fecha;
    """)
    datos = cursor.fetchall()
    cursor.close()
    conn.close()

    # Imprimir datos para verificar
    print("Datos recuperados:", datos)

    # Preparar los datos para el gráfico
    import pandas as pd
    df = pd.DataFrame(datos, columns=['Fecha', 'Ticker', 'Precio', 'Tipo', 'Cantidad'])

    # Calcular rendimientos
    rendimientos = []
    for ticker in df['Ticker'].unique():
        df_ticker = df[df['Ticker'] == ticker].sort_values('Fecha')
        precio_inicial = df_ticker.iloc[0]['Precio'] if not df_ticker.empty else 0
        df_ticker['Rendimiento (%)'] = ((df_ticker['Precio'] - precio_inicial) / precio_inicial) * 100
        rendimientos.append(df_ticker)

    df_rendimientos = pd.concat(rendimientos)

    # Crear gráfico con Plotly
    import plotly.express as px
    fig = px.line(
        df_rendimientos,
        x='Fecha',
        y='Rendimiento (%)',
        color='Ticker',
        title='Rendimiento Total de Acciones por Ticker',
        labels={'Rendimiento (%)': 'Rendimiento (%)', 'Fecha': 'Fecha'}
    )

    graph_html = pio.to_html(fig, full_html=False)

    # Renderizar el gráfico en una nueva plantilla
    return render_template('acciones/acciones_rendimiento.html', graph=graph_html)