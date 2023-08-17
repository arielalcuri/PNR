import sqlite3
from flask import Flask, render_template, request, g, jsonify, redirect, url_for
import pandas as pd
from flask import send_file
from io import BytesIO
import requests

app = Flask(__name__, static_folder='static')  # Agrega la configuración para servir archivos estáticos


# Definir la ruta de éxito
@app.route('/exito')
def exito():
    return render_template('exito.html')


@app.route('/exitopersona')
def exitopersona():
    return render_template('exitopersona.html')

DATABASE_PERSONAS = 'personas.db'
DATABASE = 'casos.db'


def get_db_personas():
    db = getattr(g, '_database_personas', None)
    if db is None:
        db = g._database_personas = sqlite3.connect(DATABASE_PERSONAS)
        db.row_factory = sqlite3.Row  # Esto permite acceder a las columnas por nombre
    return db

@app.teardown_appcontext
def close_connection_personas(exception):
    db = getattr(g, '_database_personas', None)
    if db is not None:
        db.close()

conn_personas = sqlite3.connect('casos.db')

def get_db():
    db = getattr(g, '_database_casos', None)
    if db is None:
        db = g._database_casos = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Conectarse a la base de datos (si no existe, la creará automáticamente)
conn = sqlite3.connect('casos.db')

# Crear una tabla llamada "casos" si aún no existe  
conn.execute('''CREATE TABLE IF NOT EXISTS casos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                carpeta_pn TEXT NOT NULL,
                ley_marco TEXT NOT NULL,
                num_causa TEXT NOT NULL,
                caratulado TEXT NOT NULL,
                via_ingreso TEXT NOT NULL,
                mail_pnr TEXT,
                num_expediente_gde TEXT,
                num_whatsapp TEXT,
                direccion_correo_postal TEXT,
                procedencia TEXT NOT NULL,
                fecha_recepcion TEXT NOT NULL,
                hora_recepcion TEXT NOT NULL,
                oficio_nota TEXT,
                fecha_oficio_nota TEXT,
                documento TEXT NOT NULL
                )''')
conn.close()


# Crear una tabla llamada "personas" si aún no existe
with app.app_context():
    conn_personas = get_db_personas()
    conn_personas.execute('''CREATE TABLE IF NOT EXISTS personas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    apellido TEXT NOT NULL,
                    fecha_nacimiento DATE,
                    genero TEXT,
                    email TEXT,
                    alias TEXT,
                    tipo_documento TEXT,
                    numero_documento TEXT,
                    telefono_movil TEXT,
                    telefono_fijo TEXT,
                    pais_origen TEXT,
                    provincia_origen TEXT,
                    localidad_origen TEXT,
                    barrio_origen TEXT,
                    pais_residencia TEXT,
                    provincia_residencia TEXT,
                    localidad_residencia TEXT,
                    barrio_residencia TEXT,
                    pais_domicilio TEXT,
                    provincia_domicilio TEXT,
                    localidad_domicilio TEXT,
                    barrio_domicilio TEXT,
                    calle TEXT,
                    altura TEXT,
                    piso TEXT,
                    departamento TEXT
                 )''')
    conn_personas.close()

# Ruta para la página de inicio
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/crear_caso', methods=['GET', 'POST'])
def crear_caso():
    if request.method == 'POST':
        try:
            # Obtener una conexión a la base de datos
            conn = get_db()
            cursor = conn.cursor()

            # Obtener los datos del formulario
            carpeta_pn = request.form['carpeta_pn']
            num_causa = request.form['num_causa']
            caratulado = request.form['caratulado']
            ley_marco = request.form['ley_marco']
            via_ingreso = request.form['via_ingreso']
            mail_pnr = request.form.get('mail_pnr', None)
            num_expediente_gde = request.form.get('num_expediente_gde', None)
            num_whatsapp = request.form.get('num_whatsapp', None)
            direccion_correo_postal = request.form.get('direccion_correo_postal', None)
            procedencia = request.form['procedencia']
            fecha_recepcion = request.form['fecha_recepcion']
            hora_recepcion = request.form['hora_recepcion']
            fecha_oficio_nota = request.form.get('fecha_oficio_nota', None)
            documento = request.form['documento']

            # Insertar el caso en la tabla "casos"
            cursor.execute('''INSERT INTO casos (carpeta_pn, num_causa,
                            caratulado, ley_marco, via_ingreso, mail_pnr, num_expediente_gde,
                            num_whatsapp, direccion_correo_postal, procedencia, fecha_recepcion,
                            hora_recepcion, fecha_oficio_nota, documento) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                            (carpeta_pn, num_causa, caratulado, ley_marco,
                            via_ingreso, mail_pnr, num_expediente_gde, num_whatsapp, direccion_correo_postal,
                            procedencia, fecha_recepcion, hora_recepcion, fecha_oficio_nota, documento))


            # Obtener el ID asignado al nuevo caso
            new_case_id = cursor.lastrowid

            # Guardar los cambios y cerrar la conexión
            conn.commit()

            # Pasar el ID asignado a la plantilla de éxito
            return render_template('exito.html', case_id=new_case_id)
        except Exception as e:
            print("Error:", e)
            return render_template('crear_caso.html')

    else:
        # Código para manejar la solicitud GET
        return render_template('crear_caso.html')




@app.route('/buscar_casos_por_num_causa')
def buscar_casos_por_num_causa():
    num_causa = request.args.get('num_causa', '')

    # Obtener una conexión a la base de datos
    conn = get_db()
    cursor = conn.cursor()

    # Buscar casos que coincidan con el número de causa
    cursor.execute("SELECT num_causa FROM casos WHERE num_causa LIKE ?", ('%' + num_causa + '%',))
    casos = cursor.fetchall()

    # Cerrar la conexión a la base de datos
    conn.close()

    # Devolver los resultados como un objeto JSON
    return jsonify(casos)

    

@app.route('/buscar_caso', methods=['GET', 'POST'])
def buscar_caso():
    if request.method == 'POST':
        buscar_texto = request.form['buscar_texto']
        try:
            # Obtener una conexión a la base de datos
            conn = get_db()
            cursor = conn.cursor()

            # Realizar la búsqueda en la base de datos
            cursor.execute('''
                SELECT * FROM casos
                WHERE 
                carpeta_pn LIKE ? OR
                ley_marco LIKE ? OR
                num_causa LIKE ? OR
                caratulado LIKE ? OR
                via_ingreso LIKE ? OR
                mail_pnr LIKE ? OR
                num_expediente_gde LIKE ? OR
                num_whatsapp LIKE ? OR
                direccion_correo_postal LIKE ? OR
                procedencia LIKE ? OR
                fecha_recepcion LIKE ? OR
                hora_recepcion LIKE ? OR
                oficio_nota LIKE ? OR
                fecha_oficio_nota LIKE ? OR
                documento LIKE ?
            ''', tuple(['%' + buscar_texto + '%'] * 15))
            casos = cursor.fetchall()

            # Cerrar la conexión
            conn.close()

            # Pasar los resultados de la búsqueda a la plantilla
            return render_template('buscar_caso.html', casos=casos)
        except Exception as e:
            # En caso de error, imprimirlo en la consola y mostrar un mensaje de error en la plantilla
            print(e)
            error_message = "Ha ocurrido un error al buscar el caso."
            return render_template('buscar_caso.html', error_message=error_message)
    else:
        # Código para manejar la solicitud GET
        return render_template('buscar_caso.html')



# Importar librerías y configuraciones anteriores

@app.route('/editar_caso/<int:caso_id>', methods=['GET', 'POST'])
def editar_caso(caso_id):
    if request.method == 'POST':
        try:
            # Obtener una conexión a la base de datos
            conn = get_db()
            cursor = conn.cursor()

            # Obtener los datos del formulario
            carpeta_pn = request.form['carpeta_pn']
            # Otros campos de edición aquí

            # Verificar si el campo NOTA/OFICIO N° está vacío
            oficio_nota = request.form['oficio_nota']
            if not oficio_nota:
                oficio_nota = None

            # Obtener los datos del formulario
            carpeta_pn = request.form['carpeta_pn']
            ley_marco = request.form['ley_marco']
            num_causa = request.form['num_causa']
            caratulado = request.form['caratulado']
            via_ingreso = request.form['via_ingreso']
            mail_pnr = request.form['mail_pnr']
            num_expediente_gde = request.form['num_expediente']
            num_whatsapp = request.form['num_whatsapp']
            direccion_correo_postal = request.form['direccion_postal']
            procedencia = request.form['procedencia']
            fecha_recepcion = request.form['fecha_recepcion']
            hora_recepcion = request.form['hora_recepcion']
            oficio_nota = request.form['oficio_nota']
            fecha_oficio_nota = request.form['fecha_oficio_nota']
            documento = request.form['documento']

            # Actualizar el caso en la tabla "casos"
            cursor.execute('''
                UPDATE casos SET 
                carpeta_pn=?, ley_marco=?, num_causa=?, caratulado=?, via_ingreso=?, 
                mail_pnr=?, num_expediente_gde=?, num_whatsapp=?, direccion_correo_postal=?, 
                procedencia=?, fecha_recepcion=?, hora_recepcion=?, oficio_nota=?, fecha_oficio_nota=?, documento=?
                WHERE id=?
            ''', (
                carpeta_pn, ley_marco, num_causa, caratulado, via_ingreso, 
                mail_pnr, num_expediente_gde, num_whatsapp, direccion_correo_postal, 
                procedencia, fecha_recepcion, hora_recepcion, oficio_nota, fecha_oficio_nota, documento,
                caso_id
            ))

            # Guardar los cambios y cerrar la conexión
            conn.commit()

            return redirect(url_for('buscar_caso'))  # Redireccionar a la lista de casos
        except Exception as e:
            print("Error:", e)
            # Manejar el error y renderizar el formulario nuevamente si es necesario
            conn.rollback()
            return render_template('editar_caso.html', case_id=caso_id, caso=cursor.fetchone())

    else:
        # Obtener los datos del caso de la base de datos usando el ID
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''SELECT * FROM casos WHERE id=?''', (caso_id,))
        datos_del_caso = cursor.fetchone()

        return render_template('editar_caso.html', case_id=caso_id, caso=datos_del_caso)

@app.route('/eliminar_caso/<int:caso_id>', methods=['GET', 'POST'])
def eliminar_caso(caso_id):
    if request.method == 'POST':
        try:
            connection = sqlite3.connect('casos.db')
            cursor = connection.cursor()
            cursor.execute("DELETE FROM casos WHERE id=?", (caso_id,))
            connection.commit()
            connection.close()
            return redirect(url_for('buscar_caso'))
        except sqlite3.Error as e:
            print("Error al eliminar el caso:", e)
            return render_template('error.html', mensaje="Error al eliminar el caso.")
    else:
        return render_template('eliminar_caso.html', caso_id=caso_id)



@app.route('/crear_intervencion', methods=['GET', 'POST'])
def crear_intervencion():
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        fecha = request.form['fecha']
        caso_id = request.form['caso_id']
        
        # Aquí deberías insertar la nueva intervención en la base de datos,
        # asociada al caso correspondiente según el caso_id
        
        # Luego, puedes redirigir a otra página o mostrar un mensaje de éxito
        
    return render_template('crear_intervencion.html')



@app.route('/descargar_casos_excel')
def descargar_casos_excel():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM casos')
    casos = cursor.fetchall()
    conn.close()

    # Crear un DataFrame de pandas con los resultados
    df = pd.DataFrame(casos, columns=['ID CASO','CARPETA PNR','LEY MARCO','NÚMERO DE CAUSA JUDICIAL','CARATULADO','VIA DE INGRESO','MAIL DEL PNR','N° EXPEDIENTE GDE','N° WHASTAPP','DIRECCIÓN CORREO POSTAL','PROCEDENCIA','FECHA DE RECEPCIÓN','HORA DE RECEPCIÓN','NOTA/OFICIO N°','FECHA OFICIO/NOTA', 'TIPO DE DOCUMENTO'
])

    # Crear un archivo Excel en memoria
    excel_file = BytesIO()
    with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Casos', index=False)

    # Preparar el archivo Excel para la descarga
    excel_file.seek(0)
    return send_file(excel_file, as_attachment=True, download_name='casos.xlsx')

# Ruta para mostrar el formulario de crear persona
@app.route('/crear_persona', methods=['GET', 'POST'])
def crear_persona():
    if request.method == 'POST':
        try:
            conn_personas = get_db_personas()
            cursor = conn_personas.cursor()
            
            # Validación de campos obligatorios
            nombre = request.form.get('nombre')
            apellido = request.form.get('apellido')
            if not nombre or not apellido:
                raise ValueError("Nombre y apellido son campos obligatorios")


            nombre = request.form['nombre']
            apellido = request.form['apellido']
            fecha_nacimiento = request.form['fecha_nacimiento']
            genero = request.form['genero']
            email = request.form['email']
            alias = request.form['alias']
            tipo_documento = request.form['tipo_documento']
            numero_documento = request.form['numero_documento']
            telefono_movil = request.form['telefono_movil']
            telefono_fijo = request.form['telefono_fijo']
            pais_origen = request.form['pais_origen']
            provincia_origen = request.form['provincia_origen']
            localidad_origen = request.form['localidad_origen']
            barrio_origen = request.form['barrio_origen']
            pais_residencia = request.form['pais_residencia']
            provincia_residencia = request.form['provincia_residencia']
            localidad_residencia = request.form['localidad_residencia']
            barrio_residencia = request.form['barrio_residencia']
            pais_domicilio = request.form['pais_domicilio']
            provincia_domicilio = request.form['provincia_domicilio']
            localidad_domicilio = request.form['localidad_domicilio']
            barrio_domicilio = request.form['barrio_domicilio']
            calle = request.form['calle']
            altura = request.form['altura']
            piso = request.form['piso']
            departamento = request.form['departamento']
            
            cursor.execute('''INSERT INTO personas (
                                nombre, apellido, fecha_nacimiento, genero, email, alias,
                                tipo_documento, numero_documento, telefono_movil, telefono_fijo,
                                pais_origen, provincia_origen, localidad_origen, barrio_origen,
                                pais_residencia, provincia_residencia, localidad_residencia, barrio_residencia,
                                pais_domicilio, provincia_domicilio, localidad_domicilio, barrio_domicilio,
                                calle, altura, piso, departamento
                             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                           (nombre, apellido, fecha_nacimiento, genero, email, alias,
                            tipo_documento, numero_documento, telefono_movil, telefono_fijo,
                            pais_origen, provincia_origen, localidad_origen, barrio_origen,
                            pais_residencia, provincia_residencia, localidad_residencia, barrio_residencia,
                            pais_domicilio, provincia_domicilio, localidad_domicilio, barrio_domicilio,
                            calle, altura, piso, departamento))

            conn_personas.commit()
            
            cursor.close()  # Cerrar el cursor
            conn_personas.close()  # Cerrar la conexión a la base de datos

            return redirect(url_for('exitopersona'))
        except Exception as e:
            print("Error:", e)
            return render_template('crear_persona.html')

    return render_template('crear_persona.html')



@app.route('/buscar_persona', methods=['GET', 'POST'])
def buscar_persona():
    if request.method == 'POST':
        # Obtener los valores de los campos del formulario
        filters = {
            'nombre': request.form.get('nombre'),
            'apellido': request.form.get('apellido'),
            'fecha_nacimiento': request.form.get('fecha_nacimiento'),
            'genero': request.form.get('genero'),
            'email': request.form.get('email'),
            'alias': request.form.get('alias'),
            'tipo_documento': request.form.get('tipo_documento'),
            'numero_documento': request.form.get('numero_documento'),
            'telefono_movil': request.form.get('telefono_movil'),
            'telefono_fijo': request.form.get('telefono_fijo'),
            'pais_origen': request.form.get('pais_origen'),
            'provincia_origen': request.form.get('provincia_origen'),
            'localidad_origen': request.form.get('localidad_origen'),
            'barrio_origen': request.form.get('barrio_origen'),
            'pais_residencia': request.form.get('pais_residencia'),
            'provincia_residencia': request.form.get('provincia_residencia'),
            'localidad_residencia': request.form.get('localidad_residencia'),
            'barrio_residencia': request.form.get('barrio_residencia'),
            'pais_domicilio': request.form.get('pais_domicilio'),
            'provincia_domicilio': request.form.get('provincia_domicilio'),
            'localidad_domicilio': request.form.get('localidad_domicilio'),
            'barrio_domicilio': request.form.get('barrio_domicilio'),
            'calle': request.form.get('calle'),
            'altura': request.form.get('altura'),
            'piso': request.form.get('piso'),
            'departamento': request.form.get('departamento')
        }

        try:
            # Obtener una conexión a la base de datos de personas
            conn_personas = get_db_personas()
            cursor = conn_personas.cursor()

            # Construir la consulta SQL basada en los filtros
            query = 'SELECT * FROM personas WHERE 1=1'
            values = []

            for field, value in filters.items():
                if value:
                    query += f' AND {field} LIKE ?'
                    values.append('%' + value + '%')

            # Ejecutar la consulta
            cursor.execute(query, values)
            personas = cursor.fetchall()

            # Cerrar la conexión a la base de datos de personas
            conn_personas.close()

            # Pasar los resultados de la búsqueda a la plantilla
            return render_template('buscar_persona.html', personas=personas, filters=filters)
        except Exception as e:
            # En caso de error, imprimirlo en la consola y mostrar un mensaje de error en la plantilla
            print(e)
            error_message = "Ha ocurrido un error al buscar la persona."
            return render_template('buscar_persona.html', error_message=error_message)
    else:
        # Código para manejar la solicitud GET
        filters = request.args.to_dict()
        personas = None
        # Puedes agregar aquí código para manejar la solicitud GET con filtros
        return render_template('buscar_persona.html', personas=personas, filters=filters)

@app.route('/editar_persona/<int:persona_id>', methods=['GET', 'POST'])
def editar_persona(persona_id):
    if request.method == 'POST':
        # Obtener los datos actualizados del formulario
        datos_actualizados = {
            'nombre': request.form.get('nombre'),
            'apellido': request.form.get('apellido'),
            'fecha_nacimiento': request.form.get('fecha_nacimiento'),
            'genero': request.form.get('genero'),
            'email': request.form.get('email'),
            'alias': request.form.get('alias'),
            'tipo_documento': request.form.get('tipo_documento'),
            'numero_documento': request.form.get('numero_documento'),
            'telefono_movil': request.form.get('telefono_movil'),
            'telefono_fijo': request.form.get('telefono_fijo'),
            'pais_origen': request.form.get('pais_origen'),
            'provincia_origen': request.form.get('provincia_origen'),
            'localidad_origen': request.form.get('localidad_origen'),
            'barrio_origen': request.form.get('barrio_origen'),
            'pais_residencia': request.form.get('pais_residencia'),
            'provincia_residencia': request.form.get('provincia_residencia'),
            'localidad_residencia': request.form.get('localidad_residencia'),
            'barrio_residencia': request.form.get('barrio_residencia'),
            'pais_domicilio': request.form.get('pais_domicilio'),
            'provincia_domicilio': request.form.get('provincia_domicilio'),
            'localidad_domicilio': request.form.get('localidad_domicilio'),
            'barrio_domicilio': request.form.get('barrio_domicilio'),
            'calle': request.form.get('calle'),
            'altura': request.form.get('altura'),
            'piso': request.form.get('piso'),
            'departamento': request.form.get('departamento')
        }

        try:
            # Obtener una conexión a la base de datos de personas
            conn_personas = get_db_personas()
            cursor = conn_personas.cursor()

            # Construir la consulta SQL para actualizar la persona por su ID
            query = '''
                UPDATE personas
                SET nombre=?, apellido=?, fecha_nacimiento=?, genero=?, 
                email=?, alias=?, tipo_documento=?, numero_documento=?, 
                telefono_movil=?, telefono_fijo=?, pais_origen=?, provincia_origen=?, 
                localidad_origen=?, barrio_origen=?, pais_residencia=?, provincia_residencia=?, 
                localidad_residencia=?, barrio_residencia=?, pais_domicilio=?, provincia_domicilio=?, 
                localidad_domicilio=?, barrio_domicilio=?, calle=?, altura=?, piso=?, 
                departamento=?
                WHERE id=?
            '''
            cursor.execute(query, (*datos_actualizados.values(), persona_id))

            # Aplicar el cambio en la base de datos
            conn_personas.commit()
            conn_personas.close()

            return redirect(url_for('buscar_persona'))
        except Exception as e:
            print(e)
            error_message = "Ha ocurrido un error al editar la persona."
            return render_template('buscar_persona.html', error_message=error_message)
    else:
        # Obtener los datos actuales de la persona y prellenar el formulario
        try:
            conn_personas = get_db_personas()
            cursor = conn_personas.cursor()
            query = 'SELECT * FROM personas WHERE id = ?'
            cursor.execute(query, (persona_id,))
            persona = cursor.fetchone()
            conn_personas.close()
            return render_template('editar_persona.html', persona=persona)
        except Exception as e:
            print(e)
            error_message = "Ha ocurrido un error al cargar los datos de la persona."
            return render_template('buscar_persona.html', error_message=error_message)

@app.route('/borrar_persona/<int:persona_id>', methods=['GET', 'POST'])
def borrar_persona(persona_id):
    if request.method == 'POST':
        try:
            # Obtener una conexión a la base de datos de personas
            conn_personas = get_db_personas()
            cursor = conn_personas.cursor()

            # Construir la consulta SQL para eliminar la persona por su ID
            query = 'DELETE FROM personas WHERE id = ?'
            cursor.execute(query, (persona_id,))

            # Aplicar el cambio en la base de datos
            conn_personas.commit()
            conn_personas.close()

            return redirect(url_for('buscar_persona'))
        except sqlite3.Error as e:
            print("Error al eliminar la persona:", e)
            return render_template('error.html', mensaje="Error al eliminar la persona.")
    else:
        return render_template('eliminar_persona.html', persona_id=persona_id)
       

@app.route('/parametricas')
def parametricas():
    return render_template('parametricas.html')
    
if __name__ == '__main__':
    app.run(debug=True)
