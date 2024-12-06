from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from database import get_db_connection

# Crear el Blueprint
corredores_bp = Blueprint('corredores_bp', __name__)

@corredores_bp.route('/corredores', methods=['GET'])
@login_required
def listar_corredores():
    """
    Muestra un listado de todos los corredores registrados en la base de datos.
    """
    try:
        # Conectar a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()

        # Consultar todos los corredores
        cursor.execute("""
            SELECT ID_Entidad, Rut, Nombre, FonoMovil, Email
            FROM Entidad
            WHERE TipoEntidad = 'Corredor'
            ORDER BY Nombre ASC
            """)
        corredores = cursor.fetchall()

    except Exception as e:
        flash(f"Error al obtener los datos de los corredores: {e}", "error")
        corredores = []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    # Renderizar la plantilla con los corredores
    return render_template('configuracion/corredores/corredores.html', corredores=corredores)

@corredores_bp.route('/corredores/add', methods=['GET', 'POST'])
@login_required
def add_corredor():
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

            # Insertar en la tabla Entidad con TipoEntidad = 'Corredor'
            cursor.execute("""
                INSERT INTO Entidad (Rut, Nombre, Email, FonoFijo, FonoMovil, TipoEntidad)
                VALUES (%s, %s, %s, %s, %s, 'Corredor')
            """, (rut, nombre, email, fono_fijo, fono_movil))
            conn.commit()

            flash("Corredor agregado exitosamente.", "success")
            return redirect(url_for('listar_corredores'))
        except Exception as e:
            conn.rollback()
            flash(f"Error al agregar el corredor: {e}", "error")
        finally:
            cursor.close()
            conn.close()

    return render_template('configuracion/corredores/add_corredores.html')

@corredores_bp.route('/delete_corredor/<int:id_corredor>', methods=['POST'])
@login_required
def delete_corredor(id_corredor):
    print(f"Entrando a delete_corredor con ID: {id_corredor}")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Comprobar si el corredor existe antes de eliminar
        cursor.execute("SELECT * FROM Entidad WHERE ID_Entidad = %s AND TipoEntidad = 'Corredor'", (id_corredor,))
        corredor = cursor.fetchone()
        if not corredor:
            flash("El corredor no existe o no es del tipo 'Corredor'.", "error")
            return redirect(url_for('listar_corredors'))

        # Intentar eliminar el corredor
        cursor.execute("DELETE FROM Entidad WHERE ID_Entidad = %s AND TipoEntidad = 'Corredor'", (id_corredor,))
        conn.commit()

        print(f"Corredor eliminado: {id_corredor}")
        flash("Corredor eliminado exitosamente.", "success")
    except Exception as e:
        conn.rollback()
        print(f"Error al eliminar: {e}")
        flash(f"Error al eliminar el corredor: {e}", "error")
    finally:
        cursor.close()
        conn.close()

    # Redirigir al listado de corredores después de la eliminación
    return redirect(url_for('listar_corredores'))

@corredores_bp.route('/corredores/edit/<int:id_corredor>', methods=['GET', 'POST'])
@login_required
def edit_corredor(id_corredor):
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

            # Actualizar el corredor
            cursor.execute("""
                UPDATE Entidad
                SET Rut = %s, Nombre = %s, Email = %s, FonoFijo = %s, FonoMovil = %s
                WHERE ID_Entidad = %s AND TipoEntidad = 'Corredor'
            """, (rut, nombre, email, fono_fijo, fono_movil, id_corredor))
            conn.commit()

            flash("Corredor actualizado exitosamente.", "success")
            return redirect(url_for('listar_corredores'))

        # Obtener los datos actuales del corredor
        cursor.execute("""
            SELECT Rut, Nombre, Email, FonoFijo, FonoMovil
            FROM Entidad
            WHERE ID_Entidad = %s AND TipoEntidad = 'Corredor'
        """, (id_corredor,))
        corredor = cursor.fetchone()

        if not corredor:
            flash("Corredor no encontrado.", "error")
            return redirect(url_for('listar_corredores'))

    except Exception as e:
        if conn:
            conn.rollback()
        flash(f"Error al procesar la solicitud: {e}", "error")
        return redirect(url_for('listar_corredores'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template('configuracion/corredores/edit_corredores.html', corredor=corredor, id_corredor=id_corredor)