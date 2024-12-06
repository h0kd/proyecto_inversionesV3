from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from database import get_db_connection

# Crear el Blueprint
parametros_bp = Blueprint('parametros_bp', __name__)

@parametros_bp.route('/parametros', methods=['GET', 'POST'])
@login_required
def gestionar_parametros():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'POST':
            # Capturar datos del formulario
            nombre = request.form['nombre']
            valor = float(request.form['valor'])

            # Verificar si el parámetro existe
            cursor.execute("SELECT ID_Parametro FROM Parametros WHERE Nombre = %s", (nombre,))
            parametro = cursor.fetchone()

            if parametro:
                # Actualizar el valor del parámetro existente
                cursor.execute("""
                    UPDATE Parametros
                    SET Valor = %s, FechaActualizacion = NOW()
                    WHERE ID_Parametro = %s
                """, (valor, parametro[0]))
                flash(f"Parámetro '{nombre}' actualizado.", "success")
            else:
                # Insertar un nuevo parámetro
                cursor.execute("""
                    INSERT INTO Parametros (Nombre, Valor)
                    VALUES (%s, %s)
                """, (nombre, valor))
                flash(f"Parámetro '{nombre}' agregado.", "success")

            conn.commit()

        # Obtener todos los parámetros para mostrarlos
        cursor.execute("SELECT ID_Parametro, Nombre, Valor, FechaActualizacion FROM Parametros")
        parametros = cursor.fetchall()

    except Exception as e:
        if conn:
            conn.rollback()
        flash(f"Error al gestionar parámetros: {e}", "error")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template('configuracion/parametros/parametros.html', parametros=parametros)

@parametros_bp.route('/parametros/update', methods=['POST'])
@login_required
def actualizar_parametro():
    try:
        id_parametro = request.form['id_parametro']
        nuevo_valor = float(request.form['valor'])

        conn = get_db_connection()
        cursor = conn.cursor()

        # Actualizar el parámetro en la base de datos
        cursor.execute("""
            UPDATE Parametros
            SET Valor = %s, FechaActualizacion = NOW()
            WHERE ID_Parametro = %s
        """, (nuevo_valor, id_parametro))

        conn.commit()
        flash("Parámetro actualizado exitosamente.", "success")

    except Exception as e:
        if conn:
            conn.rollback()
        flash(f"Error al actualizar el parámetro: {e}", "error")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for('gestionar_parametros'))

@parametros_bp.route('/parametros/delete', methods=['POST'])
@login_required
def eliminar_parametro():
    try:
        id_parametro = request.form['id_parametro']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Eliminar el parámetro de la base de datos
        cursor.execute("DELETE FROM Parametros WHERE ID_Parametro = %s", (id_parametro,))
        conn.commit()

        flash("Parámetro eliminado exitosamente.", "success")

    except Exception as e:
        if conn:
            conn.rollback()
        flash(f"Error al eliminar el parámetro: {e}", "error")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for('gestionar_parametros'))