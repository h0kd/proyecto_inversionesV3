from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required # type: ignore
from database import get_db_connection

# Crear el Blueprint
clientes_bp = Blueprint('clientes_bp', __name__)

@clientes_bp.route('/clientes', methods=['GET'])
@login_required
def listar_clientes():
    """
    Muestra un listado de todas las clientes registrados en la base de datos.
    """
    try:
        # Conectar a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()

        # Consultar todos las clientes
        cursor.execute("""
            SELECT ID_Entidad, Rut, Nombre, FonoMovil, Email
            FROM EntidadComercial
            WHERE TipoEntidad = 'Cliente'
            ORDER BY Nombre ASC
            """)
        clientes = cursor.fetchall()

    except Exception as e:
        flash(f"Error al obtener los datos de las clientes: {e}", "error")
        clientes = []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    # Renderizar la plantilla con las clientes
    return render_template('configuracion/clientes/clientes.html', clientes=clientes)

@clientes_bp.route('/clientes/add', methods=['GET', 'POST'])
@login_required
def add_cliente():
    if request.method == 'POST':
        # Capturar datos del formulario
        rut = request.form['rut']
        nombre = request.form['nombre'].upper()
        fono_fijo = request.form['fono_fijo']
        fono_movil = request.form['fono_movil']
        email = request.form['email']

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Insertar en la tabla Entidad con TipoEntidad = 'Banco'
            cursor.execute("""
                INSERT INTO EntidadComercial (Rut, Nombre, FonoFijo, FonoMovil, Email, TipoEntidad)
                VALUES (%s, %s, %s, %s, %s, 'Cliente')
            """, (rut, nombre, fono_fijo, fono_movil, email))
            conn.commit()

            flash("Cliente agregada exitosamente.", "success")
            return redirect(url_for('clientes_bp.listar_clientes'))
        except Exception as e:
            conn.rollback()
            flash(f"Error al agregar la cliente: {e}", "error")
        finally:
            cursor.close()
            conn.close()

    return render_template('configuracion/clientes/add_clientes.html')

@clientes_bp.route('/clientes/edit/<int:id_cliente>', methods=['GET', 'POST'])
@login_required
def edit_cliente(id_cliente):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'POST':
            # Capturar datos del formulario
            rut = request.form['rut']
            nombre = request.form['nombre']
            email = request.form.get('email')  # Opcional
            fono_fijo = request.form.get('fono_fijo')  # Opcional
            fono_movil = request.form.get('fono_movil')  # Opcional

            # Actualizar el banco
            cursor.execute("""
                UPDATE EntidadComercial
                SET Rut = %s, Nombre = %s, Email = %s, FonoFijo = %s, FonoMovil = %s
                WHERE ID_Entidad = %s AND TipoEntidad = 'Cliente'
            """, (rut, nombre, email, fono_fijo, fono_movil, id_cliente))
            conn.commit()

            flash("Cliente actualizado exitosamente.", "success")
            return redirect(url_for('clientes_bp.listar_clientes'))

        # Obtener los datos actuales del banco
        cursor.execute("""
            SELECT Rut, Nombre, Email, FonoFijo, FonoMovil
            FROM EntidadComercial
            WHERE ID_Entidad = %s AND TipoEntidad = 'Cliente'
        """, (id_cliente,))
        cliente = cursor.fetchone()

        if not cliente:
            flash("Cliente no encontrada.", "error")
            return redirect(url_for('clientes_bp.listar_clientes'))

    except Exception as e:
        if conn:
            conn.rollback()
        flash(f"Error al procesar la solicitud: {e}", "error")
        return redirect(url_for('clientes_bp.listar_clientes'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template('configuracion/clientes/edit_clientes.html', cliente=cliente, id_cliente=id_cliente)

@clientes_bp.route('/delete_cliente/<int:id_cliente>', methods=['POST'])
@login_required
def delete_cliente(id_cliente):
    print(f"Entrando a delete_cliente con ID: {id_cliente}")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Comprobar si el banco existe antes de eliminar
        cursor.execute("SELECT * FROM EntidadComercial WHERE ID_Entidad = %s AND TipoEntidad = 'Cliente'", (id_cliente,))
        cliente = cursor.fetchone()
        if not cliente:
            flash("La cliente no existe o no es del tipo 'Banco'.", "error")
            return redirect(url_for('clientes_bp.listar_clientes'))

        # Intentar eliminar el banco
        cursor.execute("DELETE FROM EntidadComercial WHERE ID_Entidad = %s AND TipoEntidad = 'Cliente'", (id_cliente,))
        conn.commit()

        print(f"Cliente eliminada: {id_cliente}")
        flash("Cliente eliminada exitosamente.", "success")
    except Exception as e:
        conn.rollback()
        print(f"Error al eliminar: {e}")
        flash(f"Error al eliminar la cliente: {e}", "error")
    finally:
        cursor.close()
        conn.close()

    # Redirigir al listado de bancos después de la eliminación
    return redirect(url_for('clientes_bp.listar_clientes'))