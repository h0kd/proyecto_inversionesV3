from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from database import get_db_connection

# Crear el Blueprint
companias_bp = Blueprint('companias_bp', __name__)

@companias_bp.route('/companias', methods=['GET'])
@login_required
def listar_companias():
    """
    Muestra un listado de todos los companias registrados en la base de datos.
    """
    try:
        # Conectar a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()

        # Consultar todos los companias
        cursor.execute("""
            SELECT ID_Entidad, Rut, Nombre, FonoMovil, Email
            FROM Entidad
            WHERE TipoEntidad = 'Compania'
            ORDER BY Nombre ASC
            """)
        companias = cursor.fetchall()

    except Exception as e:
        flash(f"Error al obtener los datos de los companias: {e}", "error")
        companias = []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    # Renderizar la plantilla con los companias
    return render_template('configuracion/companias/companias.html', companias=companias)

@companias_bp.route('/companias/add', methods=['GET', 'POST'])
@login_required
def add_compania():
    if request.method == 'POST':
        # Capturar datos del formulario
        rut = request.form['rut']
        nombre = request.form['nombre'].upper()
        email = request.form.get('email')  # Opcional
        fono_fijo = request.form.get('fono_fijo')  # Opcional
        fono_movil = request.form.get('fono_movil')  # Opcional

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Insertar en la tabla Entidad con TipoEntidad = 'compania'
            cursor.execute("""
                INSERT INTO Entidad (Rut, Nombre, Email, FonoFijo, FonoMovil, TipoEntidad)
                VALUES (%s, %s, %s, %s, %s, 'Compania')
            """, (rut, nombre, email, fono_fijo, fono_movil))
            conn.commit()

            flash("Compania agregado exitosamente.", "success")
            return redirect(url_for('listar_companias'))
        except Exception as e:
            conn.rollback()
            flash(f"Error al agregar el compania: {e}", "error")
        finally:
            cursor.close()
            conn.close()

    return render_template('configuracion/companias/add_companias.html')

@companias_bp.route('/delete_compania/<int:id_compania>', methods=['POST'])
@login_required
def delete_compania(id_compania):
    print(f"Entrando a delete_compania con ID: {id_compania}")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Comprobar si el compania existe antes de eliminar
        cursor.execute("SELECT * FROM Entidad WHERE ID_Entidad = %s AND TipoEntidad = 'Compania'", (id_compania,))
        compania = cursor.fetchone()
        if not compania:
            flash("El compania no existe o no es del tipo 'Compania'.", "error")
            return redirect(url_for('listar_companias'))

        # Intentar eliminar el compania
        cursor.execute("DELETE FROM Entidad WHERE ID_Entidad = %s AND TipoEntidad = 'Compania'", (id_compania,))
        conn.commit()

        print(f"Compania eliminado: {id_compania}")
        flash("Compania eliminado exitosamente.", "success")
    except Exception as e:
        conn.rollback()
        print(f"Error al eliminar: {e}")
        flash(f"Error al eliminar el compania: {e}", "error")
    finally:
        cursor.close()
        conn.close()

    # Redirigir al listado de companias después de la eliminación
    return redirect(url_for('listar_companias'))

@companias_bp.route('/companias/edit/<int:id_compania>', methods=['GET', 'POST'])
@login_required
def edit_compania(id_compania):
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

            # Actualizar el compania
            cursor.execute("""
                UPDATE Entidad
                SET Rut = %s, Nombre = %s, Email = %s, FonoFijo = %s, FonoMovil = %s
                WHERE ID_Entidad = %s AND TipoEntidad = 'Compania'
            """, (rut, nombre, email, fono_fijo, fono_movil, id_compania))
            conn.commit()

            flash("Compania actualizado exitosamente.", "success")
            return redirect(url_for('listar_companias'))

        # Obtener los datos actuales del compania
        cursor.execute("""
            SELECT Rut, Nombre, Email, FonoFijo, FonoMovil
            FROM Entidad
            WHERE ID_Entidad = %s AND TipoEntidad = 'Compania'
        """, (id_compania,))
        compania = cursor.fetchone()

        if not compania:
            flash("Compania no encontrado.", "error")
            return redirect(url_for('listar_companias'))

    except Exception as e:
        if conn:
            conn.rollback()
        flash(f"Error al procesar la solicitud: {e}", "error")
        return redirect(url_for('listar_companias'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template('configuracion/companias/edit_companias.html', compania=compania, id_compania=id_compania)