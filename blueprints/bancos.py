from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required # type: ignore
from database import get_db_connection

# Crear el Blueprint
bancos_bp = Blueprint('bancos_bp', __name__)


@bancos_bp.route('/bancos', methods=['GET'])
@login_required
def listar_bancos():
    """
    Muestra un listado de todos los bancos registrados en la base de datos.
    """
    try:
        # Conectar a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()

        # Consultar todos los bancos
        cursor.execute("""
            SELECT ID_Entidad, Rut, Nombre, FonoMovil, Email
            FROM Entidad
            WHERE TipoEntidad = 'Banco'
            ORDER BY Nombre ASC
            """)
        bancos = cursor.fetchall()

    except Exception as e:
        flash(f"Error al obtener los datos de los bancos: {e}", "error")
        bancos = []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    # Renderizar la plantilla con los bancos
    return render_template('configuracion/bancos/bancos.html', bancos=bancos)

@bancos_bp.route('/delete_banco/<int:id_banco>', methods=['POST'])
@login_required
def delete_banco(id_banco):
    print(f"Entrando a delete_banco con ID: {id_banco}")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Comprobar si el banco existe antes de eliminar
        cursor.execute("SELECT * FROM Entidad WHERE ID_Entidad = %s AND TipoEntidad = 'Banco'", (id_banco,))
        banco = cursor.fetchone()
        if not banco:
            flash("El banco no existe o no es del tipo 'Banco'.", "error")
            return redirect(url_for('listar_bancos'))

        # Intentar eliminar el banco
        cursor.execute("DELETE FROM Entidad WHERE ID_Entidad = %s AND TipoEntidad = 'Banco'", (id_banco,))
        conn.commit()

        print(f"Banco eliminado: {id_banco}")
        flash("Banco eliminado exitosamente.", "success")
    except Exception as e:
        conn.rollback()
        print(f"Error al eliminar: {e}")
        flash(f"Error al eliminar el banco: {e}", "error")
    finally:
        cursor.close()
        conn.close()

    # Redirigir al listado de bancos después de la eliminación
    return redirect(url_for('bancos_bp.listar_bancos'))

@bancos_bp.route('/bancos/add', methods=['GET', 'POST'])
@login_required
def add_banco():
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

            # Insertar en la tabla Entidad con TipoEntidad = 'Banco'
            cursor.execute("""
                INSERT INTO Entidad (Rut, Nombre, Email, FonoFijo, FonoMovil, TipoEntidad)
                VALUES (%s, %s, %s, %s, %s, 'Banco')
            """, (rut, nombre, email, fono_fijo, fono_movil))
            conn.commit()

            flash("Banco agregado exitosamente.", "success")
            return redirect(url_for('bancos_bp.listar_bancos'))
        except Exception as e:
            conn.rollback()
            flash(f"Error al agregar el banco: {e}", "error")
        finally:
            cursor.close()
            conn.close()

    return render_template('configuracion/bancos/add_bancos.html')

@bancos_bp.route('/bancos/edit/<int:id_banco>', methods=['GET', 'POST'])
@login_required
def edit_banco(id_banco):
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
                UPDATE Entidad
                SET Rut = %s, Nombre = %s, Email = %s, FonoFijo = %s, FonoMovil = %s
                WHERE ID_Entidad = %s AND TipoEntidad = 'Banco'
            """, (rut, nombre, email, fono_fijo, fono_movil, id_banco))
            conn.commit()

            flash("Banco actualizado exitosamente.", "success")
            return redirect(url_for('bancos_bp.listar_bancos'))

        # Obtener los datos actuales del banco
        cursor.execute("""
            SELECT Rut, Nombre, Email, FonoFijo, FonoMovil
            FROM Entidad
            WHERE ID_Entidad = %s AND TipoEntidad = 'Banco'
        """, (id_banco,))
        banco = cursor.fetchone()

        if not banco:
            flash("Banco no encontrado.", "error")
            return redirect(url_for('bancos_bp.listar_bancos'))

    except Exception as e:
        if conn:
            conn.rollback()
        flash(f"Error al procesar la solicitud: {e}", "error")
        return redirect(url_for('bancos_bp.listar_bancos'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template('configuracion/bancos/edit_banco.html', banco=banco, id_banco=id_banco)