import sqlite3
from flask import Flask, render_template, request, g, jsonify, redirect, url_for, flash
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
DATABASE_AUTO_DESIGNADO = 'auto_designado.db'
DATABASE_ATENCION_DE_SALUD = 'atencion_de_salud.db'
DATABASE_CANALES_DE_INGRESO = 'canales_de_ingeso.db'
DATABASE_FUERZAS_DE_SEGURIDAD = 'fuerzas_de_seguridad.db'
DATABASE_GENEROS = 'generos.db'
DATABASE_LUGARES_EXPLOTACION = 'lugares_explotacion.db'
DATABASE_NIVELES_INSTRUCCION = 'niveles_instruccion.db'
DATABASE_OFICINAS_ACTUANTES = 'oficinas_actuantes.db'
DATABASE_PERSONAL_POLICIAL_PNR = 'personal_policial_pnr.db'
DATABASE_PUNTOS_FOCALES = 'puntos_focales.db'
DATABASE_RESERVAS = 'reservas.db'
DATABASE_ROLES_PERSONAS = 'roles_personas.db'
DATABASE_TIPOS_INTERVENCIONES = 'tipos_intervenciones.db'
DATABASE_TIPOS_ARTICULACIONES = 'tipos_articulaciones.db'
DATABASE_TIPOS_DOCUMENTOS = 'tipos_documentos.db'
DATABASE_TIPOLOGIAS = 'tipologias.db'
DATABASE_roles = 'tipologias.db'


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

conn_personas = sqlite3.connect('personas.db')

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
                    genero TEXT NOT NULL,
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

            # Obtener registros de tipologías
            registros_tipologias = obtener_tipologias()

            # Pasar el ID asignado y las tipologías a la plantilla de éxito
            return render_template('exito.html', case_id=new_case_id, registros_tipologias=registros_tipologias)
        except Exception as e:
            print("Error:", e)
            return render_template('crear_caso.html', registros_tipologias=obtener_tipologias())

    else:
        # Obtener registros de tipologías para mostrar en el formulario
        registros_tipologias = obtener_tipologias()

        # Código para manejar la solicitud GET
        return render_template('crear_caso.html', registros_tipologias=registros_tipologias)




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
    caso_default_value = ""  # Establece un valor predeterminado vacío

    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        fecha = request.form['fecha']
        caso_id = request.form['caso_id']
        
        # Aquí deberías insertar la nueva intervención en la base de datos,
        # asociada al caso correspondiente según el caso_id
        
        # Luego, puedes redirigir a otra página o mostrar un mensaje de éxito
        
    else:
        caso_id = request.args.get('caso_id')  # Obtener el caso_id desde la URL

        # Obtener datos del caso
        datos_caso = obtener_datos_caso(caso_id)

        # Si obtuviste datos del caso
        if datos_caso:
            # Concatenar los datos y establecer el valor predeterminado del campo "Caso"
            caso_default_value = f"{datos_caso[0]} {datos_caso[1]} {datos_caso[2]}"

    return render_template('crear_intervencion.html', caso_default_value=caso_default_value)

def obtener_abogados():
    conn = sqlite3.connect('roles.db')
    cursor = conn.cursor()
    cursor.execute('SELECT apellido_nombre FROM roles WHERE rol = "Abogado/a"')
    abogados = [row[0] for row in cursor.fetchall()]
    conn.close()
    return abogados

def obtener_lista_profesionales():
    conn = sqlite3.connect('roles.db')
    cursor = conn.cursor()
    cursor.execute('SELECT apellido_nombre FROM roles WHERE rol = "Profesional"')
    profesionales = [row[0] for row in cursor.fetchall()]
    conn.close()
    return profesionales

@app.route('/api/profesionales', methods=['GET'])
def obtener_profesionales():
    profesionales = obtener_lista_profesionales()
    return jsonify(profesionales)

@app.route('/obtener_roles')
def obtener_roles():
    abogados = obtener_abogados()
    return jsonify(abogados)

@app.route('/obtener_personal_policial')
def obtener_personal_policial_route():
    personal_policial = obtener_personal_policial_pnr()  # Cambiado el nombre de la variable
    return jsonify(personal_policial)

def obtener_personal_policial_pnr():
    conn = sqlite3.connect('personal_policial_pnr.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM personal_policial_pnr')
    personal_policial_pnr = cursor.fetchall()
    conn.close()
    return personal_policial_pnr


@app.route('/buscar_casos_por_criterios', methods=['GET'])
def buscar_casos_por_criterios():
    num_causa = request.args.get('num_causa', '')
    fecha_recepcion = request.args.get('fecha_recepcion', '')
    caratulado = request.args.get('caratulado', '')

    print(f'num_causa: {num_causa}, fecha_recepcion: {fecha_recepcion}, caratulado: {caratulado}')

    # Obtener una conexión a la base de datos
    conn = get_db()
    cursor = conn.cursor()

    # Imprimir la consulta SQL (para depuración)
    consulta_sql = "SELECT * FROM casos WHERE num_causa LIKE ? AND fecha_recepcion LIKE ? AND caratulado LIKE ?"
    print(f"Consulta SQL: {consulta_sql}")

    # Ejecutar la consulta SQL con parámetros seguros para evitar SQL injection
    cursor.execute(consulta_sql, ('%' + num_causa + '%', '%' + fecha_recepcion + '%', '%' + caratulado + '%'))
    casos = cursor.fetchall()

    # Cerrar la conexión a la base de datos
    conn.close()

    # Preparar los resultados para la autocompletación
    resultados = [{'label': f'N° de Causa: {caso[3]} - Fecha de Recepción: {caso[11]} - Carátula: {caso[4]}', 'value': caso[3]} for caso in casos]

    # Devolver los resultados como un objeto JSON
    return jsonify(resultados)


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


def obtener_datos_caso(id_caso):
    conn_casos = sqlite3.connect('casos.db')
    cursor = conn_casos.cursor()

    cursor.execute('SELECT num_causa, fecha_recepcion, caratulado FROM casos WHERE id = ?', (id_caso,))
    datos_caso = cursor.fetchone()

    cursor.close()
    conn_casos.close()

    return datos_caso


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
            return render_template('crear_persona.html', registros_generos=obtener_generos(), registros_tipos_documentos=obtener_tipos_documentos())

    # Obtener registros de géneros y tipos de documentos para mostrar en el formulario
    registros_generos = obtener_generos()
    registros_tipos_documentos = obtener_tipos_documentos()

    return render_template('crear_persona.html', registros_generos=registros_generos, registros_tipos_documentos=registros_tipos_documentos)




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


conn = sqlite3.connect('auto_designado.db')
cursor = conn.cursor()

# Crear la tabla de Auto Designado si no existe
cursor.execute('''
    CREATE TABLE IF NOT EXISTS auto_designado (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL
    )
''')

# Guardar los cambios y cerrar la conexión
conn.commit()
conn.close()


def crear_auto_designado(nombre):
    conn = sqlite3.connect('auto_designado.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO auto_designado (nombre) VALUES (?)', (nombre,))
    conn.commit()
    conn.close()


def obtener_auto_designados():
    conn = sqlite3.connect('auto_designado.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM auto_designado')
    auto_designados = cursor.fetchall()
    conn.close()
    return auto_designados


# Ejemplo de uso:
registros = obtener_auto_designados()
for registro in registros:
    print(registro)

def actualizar_auto_designado(id, nuevo_nombre):
    conn = sqlite3.connect('auto_designado.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE auto_designado SET nombre = ? WHERE id = ?', (nuevo_nombre, id))
    conn.commit()
    conn.close()

# Ejemplo de uso:
actualizar_auto_designado(1, 'Nuevo Nombre')


@app.route('/parametricas/auto_designado')
def auto_designado():
    # Obtener registros de la base de datos
    registros = obtener_auto_designados()
    
    # Renderizar la plantilla HTML y pasar los registros como contexto
    return render_template('auto_designado.html', registros=registros)

@app.route('/guardar_auto_designado', methods=['POST'])
def guardar_auto_designado():
    if request.method == 'POST':
        nombre = request.form['nombre']  # Obtén el nombre del formulario
        crear_auto_designado(nombre)  # Llama a la función para crear un registro
        return redirect('/parametricas/auto_designado')  # Redirige a la página de Auto Designado

    return 'Registro de Auto Designado guardado con éxito'

   
@app.route('/editar_auto_designado', methods=['POST'])
def editar_auto_designado():
    if request.method == 'POST':
        id = request.form['editId']
        nuevo_nombre = request.form['nuevo_nombre']
        actualizar_auto_designado(id, nuevo_nombre)
        return redirect(url_for('auto_designado'))

    return 'Registro de Auto Designado editado con éxito'     


def obtener_auto_designado_por_id(id):
    try:
        conn = sqlite3.connect('auto_designado.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM auto_designado WHERE id = ?', (id,))
        registro = cursor.fetchone()
        conn.close()
        return registro
    except Exception as e:
        return f"Error al obtener el registro por ID: {str(e)}", 500

@app.route('/eliminar_auto_designado/<int:auto_designado_id>', methods=['POST'])
def eliminar_auto_designado(auto_designado_id):
    if request.method == 'POST':
        try:
            # Obtener una conexión a la base de datos de auto designado
            conn_auto_designado = sqlite3.connect('auto_designado.db')
            cursor = conn_auto_designado.cursor()

            # Construir la consulta SQL para eliminar el auto designado por su ID
            query = 'DELETE FROM auto_designado WHERE id = ?'
            cursor.execute(query, (auto_designado_id,))

            # Aplicar el cambio en la base de datos
            conn_auto_designado.commit()
            conn_auto_designado.close()

            return "Registro eliminado correctamente"  # O puedes redirigir a otra página si lo prefieres
        except sqlite3.Error as e:
            print("Error al eliminar el registro de auto designado:", e)
            return "Error al eliminar el registro de auto designado.", 500
    else:
        # Maneja solicitudes GET si es necesario, por ejemplo, mostrando una página de confirmación
        return render_template('eliminar_auto_designado.html', auto_designado_id=auto_designado_id)




conn = sqlite3.connect('atencion_de_salud.db')
cursor = conn.cursor()

# Crear la tabla de Atención de Salud si no existe
cursor.execute('''
    CREATE TABLE IF NOT EXISTS atencion_de_salud (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL
    )
''')

# Guardar los cambios y cerrar la conexión
conn.commit()
conn.close()


def crear_atencion_de_salud(nombre):
    conn = sqlite3.connect('atencion_de_salud.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO atencion_de_salud (nombre) VALUES (?)', (nombre,))
    conn.commit()
    conn.close()


def obtener_atencion_de_salud():
    conn = sqlite3.connect('atencion_de_salud.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM atencion_de_salud')
    atencion_de_salud = cursor.fetchall()
    conn.close()
    return atencion_de_salud


# Ejemplo de uso:
registros = obtener_atencion_de_salud()
for registro in registros:
    print(registro)


def actualizar_atencion_de_salud(id, nuevo_nombre):
    conn = sqlite3.connect('atencion_de_salud.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE atencion_de_salud SET nombre = ? WHERE id = ?', (nuevo_nombre, id))
    conn.commit()
    conn.close()

# Ejemplo de uso:
actualizar_atencion_de_salud(1, 'Nuevo Nombre')

@app.route('/parametricas/atencion_de_salud')
def atencion_de_salud():
    # Obtener registros de la base de datos
    registros = obtener_atencion_de_salud()
    
    # Renderizar la plantilla HTML y pasar los registros como contexto
    return render_template('atencion_de_salud.html', registros=registros)

@app.route('/guardar_atencion_de_salud', methods=['POST'])
def guardar_atencion_de_salud():
    if request.method == 'POST':
        nombre = request.form['nombre']  # Obtén el nombre del formulario
        crear_atencion_de_salud(nombre)  # Llama a la función para crear un registro
        return redirect('/parametricas/atencion_de_salud')  # Redirige a la página de Atención de Salud

    return 'Registro de Atención de Salud guardado con éxito'

@app.route('/editar_atencion_de_salud', methods=['POST'])
def editar_atencion_de_salud():
    if request.method == 'POST':
        id = request.form['editId']
        nuevo_nombre = request.form['nuevo_nombre']
        actualizar_atencion_de_salud(id, nuevo_nombre)
        return redirect(url_for('atencion_de_salud'))

    return 'Registro de Atención de Salud editado con éxito'

def obtener_atencion_de_salud_por_id(id):
    try:
        conn = sqlite3.connect('atencion_de_salud.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM atencion_de_salud WHERE id = ?', (id,))
        registro = cursor.fetchone()
        conn.close()
        return registro
    except Exception as e:
        return f"Error al obtener el registro por ID: {str(e)}", 500

@app.route('/eliminar_atencion_de_salud/<int:atencion_de_salud_id>', methods=['POST'])
def eliminar_atencion_de_salud(atencion_de_salud_id):
    if request.method == 'POST':
        try:
            # Obtener una conexión a la base de datos de Atención de Salud
            conn_atencion_de_salud = sqlite3.connect('atencion_de_salud.db')
            cursor = conn_atencion_de_salud.cursor()

            # Construir la consulta SQL para eliminar la Atención de Salud por su ID
            query = 'DELETE FROM atencion_de_salud WHERE id = ?'
            cursor.execute(query, (atencion_de_salud_id,))

            # Aplicar el cambio en la base de datos
            conn_atencion_de_salud.commit()
            conn_atencion_de_salud.close()

            return "Registro eliminado correctamente"  # O puedes redirigir a otra página si lo prefieres
        except sqlite3.Error as e:
            print("Error al eliminar el registro de Atención de Salud:", e)
            return "Error al eliminar el registro de Atención de Salud.", 500
    else:
        # Maneja solicitudes GET si es necesario, por ejemplo, mostrando una página de confirmación
        return render_template('eliminar_atencion_de_salud.html', atencion_de_salud_id=atencion_de_salud_id)


conn = sqlite3.connect('canales_de_ingreso.db')
cursor = conn.cursor()

# Crear la tabla de Canales de Ingreso si no existe
cursor.execute('''
    CREATE TABLE IF NOT EXISTS canales_de_ingreso (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL
    )
''')

# Guardar los cambios y cerrar la conexión
conn.commit()
conn.close()

def crear_canal_ingreso(nombre):
    conn = sqlite3.connect('canales_de_ingreso.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO canales_de_ingreso (nombre) VALUES (?)', (nombre,))
    conn.commit()
    conn.close()

def obtener_canales_ingreso():
    conn = sqlite3.connect('canales_de_ingreso.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM canales_de_ingreso')
    canales_ingreso = cursor.fetchall()
    conn.close()
    return canales_ingreso

def actualizar_canal_ingreso(id, nuevo_nombre):
    conn = sqlite3.connect('canales_de_ingreso.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE canales_de_ingreso SET nombre = ? WHERE id = ?', (nuevo_nombre, id))
    conn.commit()
    conn.close()

def obtener_canal_ingreso_por_id(id):
    try:
        conn = sqlite3.connect('canales_de_ingreso.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM canales_de_ingreso WHERE id = ?', (id,))
        registro = cursor.fetchone()
        conn.close()
        return registro
    except Exception as e:
        return f"Error al obtener el registro por ID: {str(e)}", 500

def eliminar_canal_ingreso(id):
    try:
        conn = sqlite3.connect('canales_de_ingreso.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM canales_de_ingreso WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        return "Registro eliminado correctamente"
    except Exception as e:
        return f"Error al eliminar el registro: {str(e)}", 500

@app.route('/parametricas/canales_de_ingreso')
def canales_de_ingreso():
    # Obtener registros de la base de datos
    registros = obtener_canales_ingreso()
    
    # Renderizar la plantilla HTML y pasar los registros como contexto
    return render_template('canales_de_ingreso.html', registros=registros)

@app.route('/guardar_canal_ingreso', methods=['POST'])
def guardar_canal_ingreso():
    if request.method == 'POST':
        nombre = request.form['nombre']  # Obtén el nombre del formulario
        crear_canal_ingreso(nombre)  # Llama a la función para crear un registro
        return redirect('/parametricas/canales_de_ingreso')  # Redirige a la página de Canales de Ingreso

    return 'Registro de Canal de Ingreso guardado con éxito'

@app.route('/editar_canal_ingreso', methods=['POST'])
def editar_canal_ingreso():
    if request.method == 'POST':
        id = request.form['editId']
        nuevo_nombre = request.form['nuevo_nombre']
        actualizar_canal_ingreso(id, nuevo_nombre)
        return redirect(url_for('canales_de_ingreso'))

    return 'Registro de Canal de Ingreso editado con éxito'

@app.route('/eliminar_canal_ingreso/<int:canal_ingreso_id>', methods=['GET', 'POST'])
def eliminar_canal_ingreso_vista(canal_ingreso_id):
    if request.method == 'POST':
        resultado = eliminar_canal_ingreso(canal_ingreso_id)
        return resultado  # Devuelve un mensaje de éxito o error

    return render_template('eliminar_canal_ingreso.html', canal_ingreso_id=canal_ingreso_id)


# Función para crear una tabla de Fuerzas de Seguridad si no existe
def crear_tabla_fuerza_seguridad():
    conn = sqlite3.connect('fuerzas_de_seguridad.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fuerzas_de_seguridad (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Llama a la función para crear la tabla al iniciar la aplicación
crear_tabla_fuerza_seguridad()

# Función para crear una Fuerza de Seguridad
def crear_fuerza_seguridad(nombre):
    conn = sqlite3.connect('fuerzas_de_seguridad.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO fuerzas_de_seguridad (nombre) VALUES (?)', (nombre,))
    conn.commit()
    conn.close()

# Función para obtener todas las Fuerzas de Seguridad
def obtener_fuerzas_seguridad():
    conn = sqlite3.connect('fuerzas_de_seguridad.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM fuerzas_de_seguridad')
    fuerzas_seguridad = cursor.fetchall()
    conn.close()
    return fuerzas_seguridad

# Ruta para mostrar la lista de Fuerzas de Seguridad
@app.route('/parametricas/fuerzas_de_seguridad')
def fuerzas_seguridad():
    # Obtener registros de la base de datos
    registros = obtener_fuerzas_seguridad()
    # Renderizar la plantilla HTML y pasar los registros como contexto
    return render_template('fuerzas_de_seguridad.html', registros=registros)

# Ruta para guardar una nueva Fuerza de Seguridad
@app.route('/guardar_fuerza_seguridad', methods=['POST'])
def guardar_fuerza_seguridad():
    if request.method == 'POST':
        nombre = request.form['nombre']  # Obtén el nombre del formulario
        crear_fuerza_seguridad(nombre)  # Llama a la función para crear un registro
        return redirect('/parametricas/fuerzas_de_seguridad')  # Redirige a la página de Fuerzas de Seguridad

    return 'Registro de Fuerza de Seguridad guardado con éxito'

# Función para actualizar una Fuerza de Seguridad por ID
def actualizar_fuerza_seguridad(id, nuevo_nombre):
    conn = sqlite3.connect('fuerzas_de_seguridad.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE fuerzas_de_seguridad SET nombre = ? WHERE id = ?', (nuevo_nombre, id))
    conn.commit()
    conn.close()

# Ruta para editar una Fuerza de Seguridad
@app.route('/editar_fuerza_seguridad', methods=['POST'])
def editar_fuerza_seguridad():
    if request.method == 'POST':
        id = request.form['editId']
        nuevo_nombre = request.form['nuevo_nombre']
        actualizar_fuerza_seguridad(id, nuevo_nombre)
        return redirect(url_for('fuerzas_seguridad'))

    return 'Registro de Fuerza de Seguridad editado con éxito'

# Función para obtener una Fuerza de Seguridad por ID
def obtener_fuerza_seguridad_por_id(id):
    try:
        conn = sqlite3.connect('fuerzas_de_seguridad.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM fuerzas_de_seguridad WHERE id = ?', (id,))
        registro = cursor.fetchone()
        conn.close()
        return registro
    except Exception as e:
        return f"Error al obtener el registro por ID: {str(e)}", 500

# Ruta para eliminar una Fuerza de Seguridad por ID
@app.route('/eliminar_fuerza_seguridad/<int:fuerza_seguridad_id>', methods=['POST'])
def eliminar_fuerza_seguridad(fuerza_seguridad_id):
    if request.method == 'POST':
        try:
            # Obtener una conexión a la base de datos de Fuerzas de Seguridad
            conn_fuerza_seguridad = sqlite3.connect('fuerzas_de_seguridad.db')
            cursor = conn_fuerza_seguridad.cursor()

            # Construir la consulta SQL para eliminar la Fuerza de Seguridad por su ID
            query = 'DELETE FROM fuerzas_de_seguridad WHERE id = ?'
            cursor.execute(query, (fuerza_seguridad_id,))

            # Aplicar el cambio en la base de datos
            conn_fuerza_seguridad.commit()
            conn_fuerza_seguridad.close()

            return "Registro eliminado correctamente"  # O puedes redirigir a otra página si lo prefieres
        except sqlite3.Error as e:
            print("Error al eliminar el registro de Fuerza de Seguridad:", e)
            return "Error al eliminar el registro de Fuerza de Seguridad.", 500
    else:
        # Maneja solicitudes GET si es necesario, por ejemplo, mostrando una página de confirmación
        return render_template('eliminar_fuerza_seguridad.html', fuerza_seguridad_id=fuerza_seguridad_id)



# Función para crear una tabla de Géneros si no existe
def crear_tabla_genero():
    conn = sqlite3.connect('generos.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS generos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Llama a la función para crear la tabla al iniciar la aplicación
crear_tabla_genero()

# Función para crear un Género
def crear_genero(nombre):
    conn = sqlite3.connect('generos.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO generos (nombre) VALUES (?)', (nombre,))
    conn.commit()
    conn.close()

# Función para obtener todos los Géneros
def obtener_generos():
    # Conectarse a la base de datos generos.db
    conn_generos = sqlite3.connect('generos.db')
    cursor = conn_generos.cursor()

    # Obtener los géneros
    cursor.execute('SELECT nombre FROM generos')
    generos = [row[0] for row in cursor.fetchall()]

    # Cerrar la conexión y retornar los géneros
    cursor.close()
    conn_generos.close()

    return generos

# Ruta para mostrar la lista de Géneros
@app.route('/parametricas/generos')
def generos():
    # Obtener registros de la base de datos
    registros = obtener_generos()
    # Renderizar la plantilla HTML y pasar los registros como contexto
    return render_template('generos.html', registros=registros)

# Ruta para guardar un nuevo Género
@app.route('/guardar_genero', methods=['POST'])
def guardar_genero():
    if request.method == 'POST':
        nombre = request.form['nombre']  # Obtén el nombre del formulario
        crear_genero(nombre)  # Llama a la función para crear un registro
        return redirect('/parametricas/generos')  # Redirige a la página de Géneros

    return 'Registro de Género guardado con éxito'

# Función para actualizar un Género por ID
def actualizar_genero(id, nuevo_nombre):
    conn = sqlite3.connect('generos.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE generos SET nombre = ? WHERE id = ?', (nuevo_nombre, id))
    conn.commit()
    conn.close()

# Ruta para editar un Género
@app.route('/editar_genero', methods=['POST'])
def editar_genero():
    if request.method == 'POST':
        id = request.form['editId']
        nuevo_nombre = request.form['nuevo_nombre']
        actualizar_genero(id, nuevo_nombre)
        return redirect(url_for('generos'))

    return 'Registro de Género editado con éxito'

# Función para obtener un Género por ID
def obtener_genero_por_id(id):
    try:
        conn = sqlite3.connect('generos.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM generos WHERE id = ?', (id,))
        registro = cursor.fetchone()
        conn.close()
        return registro
    except Exception as e:
        return f"Error al obtener el registro por ID: {str(e)}", 500

# Ruta para eliminar un Género por ID
@app.route('/eliminar_genero/<int:genero_id>', methods=['POST'])
def eliminar_genero(genero_id):
    if request.method == 'POST':
        try:
            # Obtener una conexión a la base de datos de Géneros
            conn_genero = sqlite3.connect('generos.db')
            cursor = conn_genero.cursor()

            # Construir la consulta SQL para eliminar el Género por su ID
            query = 'DELETE FROM generos WHERE id = ?'
            cursor.execute(query, (genero_id,))

            # Aplicar el cambio en la base de datos
            conn_genero.commit()
            conn_genero.close()

            return "Registro eliminado correctamente"  # O puedes redirigir a otra página si lo prefieres
        except sqlite3.Error as e:
            print("Error al eliminar el registro de Género:", e)
            return "Error al eliminar el registro de Género.", 500
    else:
        # Maneja solicitudes GET si es necesario, por ejemplo, mostrando una página de confirmación
        return render_template('eliminar_genero.html', genero_id=genero_id)

conn = sqlite3.connect('lugares_explotacion.db')
cursor = conn.cursor()

# Crear la tabla de Auto Designado si no existe
cursor.execute('''
    CREATE TABLE IF NOT EXISTS lugares_explotacion (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL
    )
''')

# Guardar los cambios y cerrar la conexión
conn.commit()
conn.close()

def crear_tabla_lugares_explotacion():
    conn = sqlite3.connect('lugares_explotacion.db')  # Reemplaza 'tu_base_de_datos.db' con el nombre de tu base de datos
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lugares_explotacion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Llama a esta función para crear la tabla si no existe
crear_tabla_lugares_explotacion()

# Ruta principal para Lugares de Explotación
@app.route('/parametricas/lugares_explotacion')
def lugares_explotacion():
    # Obtener registros de la base de datos
    registros = obtener_lugares_explotacion()
    
    # Renderizar la plantilla HTML y pasar los registros como contexto
    return render_template('lugares_explotacion.html', registros=registros)

# Ruta para guardar un nuevo registro de Lugar de Explotación
@app.route('/guardar_lugar_explotacion', methods=['POST'])
def guardar_lugar_explotacion():
    if request.method == 'POST':
        nombre = request.form['nombre']  # Obtén el nombre del formulario
        crear_lugar_explotacion(nombre)  # Llama a la función para crear un registro
        return redirect('/parametricas/lugares_explotacion')  # Redirige a la página de Lugares de Explotación

    return 'Registro de Lugar de Explotación guardado con éxito'

# Función para crear un nuevo registro de Lugar de Explotación en la base de datos
def crear_lugar_explotacion(nombre):
    conn = sqlite3.connect('lugares_explotacion.db')  # Reemplaza con el nombre de tu base de datos
    cursor = conn.cursor()
    cursor.execute('INSERT INTO lugares_explotacion (nombre) VALUES (?)', (nombre,))
    conn.commit()
    conn.close()

# Ruta para editar un registro de Lugar de Explotación
@app.route('/editar_lugar_explotacion', methods=['POST'])
def editar_lugar_explotacion():
    if request.method == 'POST':
        id = request.form['editId']
        nuevo_nombre = request.form['nuevo_nombre']
        actualizar_lugar_explotacion(id, nuevo_nombre)
        return redirect(url_for('lugares_explotacion'))

    return 'Registro de Lugar de Explotación editado con éxito'

# Función para actualizar un registro de Lugar de Explotación en la base de datos
def actualizar_lugar_explotacion(id, nuevo_nombre):
    conn = sqlite3.connect('lugares_explotacion.db')  # Reemplaza con el nombre de tu base de datos
    cursor = conn.cursor()
    cursor.execute('UPDATE lugares_explotacion SET nombre = ? WHERE id = ?', (nuevo_nombre, id))
    conn.commit()
    conn.close()

# Función para obtener registros de Lugar de Explotación desde la base de datos
def obtener_lugares_explotacion():
    conn = sqlite3.connect('lugares_explotacion.db')  # Reemplaza con el nombre de tu base de datos
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM lugares_explotacion')
    lugares_explotacion = cursor.fetchall()
    conn.close()
    return lugares_explotacion

# Ruta para eliminar un registro de Lugar de Explotación
@app.route('/eliminar_lugar_explotacion/<int:lugar_explotacion_id>', methods=['POST'])
def eliminar_lugar_explotacion(lugar_explotacion_id):
    if request.method == 'POST':
        try:
            # Obtener una conexión a la base de datos de Lugar de Explotación
            conn_lugar_explotacion = sqlite3.connect('lugares_explotacion.db')  # Reemplaza con el nombre de tu base de datos
            cursor = conn_lugar_explotacion.cursor()

            # Construir la consulta SQL para eliminar el Lugar de Explotación por su ID
            query = 'DELETE FROM lugares_explotacion WHERE id = ?'
            cursor.execute(query, (lugar_explotacion_id,))

            # Aplicar el cambio en la base de datos
            conn_lugar_explotacion.commit()
            conn_lugar_explotacion.close()

            return "Registro eliminado correctamente"  # O puedes redirigir a otra página si lo prefieres
        except sqlite3.Error as e:
            print("Error al eliminar el registro de Lugar de Explotación:", e)
            return "Error al eliminar el registro de Lugar de Explotación.", 500
    else:
        # Maneja solicitudes GET si es necesario, por ejemplo, mostrando una página de confirmación
        return render_template('eliminar_lugar_explotacion.html', lugar_explotacion_id=lugar_explotacion_id)


# Función para crear la tabla de Niveles de Instrucción si no existe
def crear_tabla_niveles_instruccion():
    conn = sqlite3.connect('niveles_instruccion.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS niveles_instruccion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Llama a esta función para crear la tabla si no existe
crear_tabla_niveles_instruccion()

# Ruta principal para Niveles de Instrucción
@app.route('/parametricas/niveles_instruccion')
def niveles_instruccion():
    # Obtener registros de la base de datos
    registros = obtener_niveles_instruccion()
    
    # Renderizar la plantilla HTML y pasar los registros como contexto
    return render_template('niveles_instruccion.html', registros=registros)

# Ruta para guardar un nuevo registro de Nivel de Instrucción
@app.route('/guardar_nivel_instruccion', methods=['POST'])
def guardar_nivel_instruccion():
    if request.method == 'POST':
        nombre = request.form['nombre']  # Obtén el nombre del formulario
        crear_nivel_instruccion(nombre)  # Llama a la función para crear un registro
        return redirect('/parametricas/niveles_instruccion')  # Redirige a la página de Niveles de Instrucción

    return 'Registro de Nivel de Instrucción guardado con éxito'

# Función para crear un nuevo registro de Nivel de Instrucción en la base de datos
def crear_nivel_instruccion(nombre):
    conn = sqlite3.connect('niveles_instruccion.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO niveles_instruccion (nombre) VALUES (?)', (nombre,))
    conn.commit()
    conn.close()

# Ruta para editar un registro de Nivel de Instrucción
@app.route('/editar_nivel_instruccion', methods=['POST'])
def editar_nivel_instruccion():
    if request.method == 'POST':
        id = request.form['editId']
        nuevo_nombre = request.form['nuevo_nombre']
        actualizar_nivel_instruccion(id, nuevo_nombre)
        return redirect(url_for('niveles_instruccion'))

    return 'Registro de Nivel de Instrucción editado con éxito'

# Función para actualizar un registro de Nivel de Instrucción en la base de datos
def actualizar_nivel_instruccion(id, nuevo_nombre):
    conn = sqlite3.connect('niveles_instruccion.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE niveles_instruccion SET nombre = ? WHERE id = ?', (nuevo_nombre, id))
    conn.commit()
    conn.close()

# Función para obtener registros de Niveles de Instrucción desde la base de datos
def obtener_niveles_instruccion():
    conn = sqlite3.connect('niveles_instruccion.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM niveles_instruccion')
    niveles_instruccion = cursor.fetchall()
    conn.close()
    return niveles_instruccion

# Ruta para eliminar un registro de Nivel de Instrucción
@app.route('/eliminar_nivel_instruccion/<int:nivel_instruccion_id>', methods=['POST'])
def eliminar_nivel_instruccion(nivel_instruccion_id):
    if request.method == 'POST':
        try:
            # Obtener una conexión a la base de datos de Nivel de Instrucción
            conn_nivel_instruccion = sqlite3.connect('niveles_instruccion.db')
            cursor = conn_nivel_instruccion.cursor()

            # Construir la consulta SQL para eliminar el Nivel de Instrucción por su ID
            query = 'DELETE FROM niveles_instruccion WHERE id = ?'
            cursor.execute(query, (nivel_instruccion_id,))

            # Aplicar el cambio en la base de datos
            conn_nivel_instruccion.commit()
            conn_nivel_instruccion.close()

            return "Registro eliminado correctamente"  # O puedes redirigir a otra página si lo prefieres
        except sqlite3.Error as e:
            print("Error al eliminar el registro de Nivel de Instrucción:", e)
            return "Error al eliminar el registro de Nivel de Instrucción.", 500
    else:
        # Maneja solicitudes GET si es necesario, por ejemplo, mostrando una página de confirmación
        return render_template('eliminar_nivel_instruccion.html', nivel_instruccion_id=nivel_instruccion_id)


# Función para crear la tabla de Oficinas Actuantes si no existe
def crear_tabla_oficinas_actuantes():
    conn = sqlite3.connect('oficinas_actuantes.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS oficinas_actuantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Llama a esta función para crear la tabla si no existe
crear_tabla_oficinas_actuantes()

# Ruta principal para Oficinas Actuantes
@app.route('/parametricas/oficinas_actuantes')
def oficinas_actuantes():
    # Obtener registros de la base de datos
    registros = obtener_oficinas_actuantes()
    
    # Renderizar la plantilla HTML y pasar los registros como contexto
    return render_template('oficinas_actuantes.html', registros=registros)

# Ruta para guardar un nuevo registro de Oficina Actuante
@app.route('/guardar_oficina_actuante', methods=['POST'])
def guardar_oficina_actuante():
    if request.method == 'POST':
        nombre = request.form['nombre']  # Obtén el nombre del formulario
        crear_oficina_actuante(nombre)  # Llama a la función para crear un registro
        return redirect('/parametricas/oficinas_actuantes')  # Redirige a la página de Oficinas Actuantes

    return 'Registro de Oficina Actuante guardado con éxito'

# Función para crear un nuevo registro de Oficina Actuante en la base de datos
def crear_oficina_actuante(nombre):
    conn = sqlite3.connect('oficinas_actuantes.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO oficinas_actuantes (nombre) VALUES (?)', (nombre,))
    conn.commit()
    conn.close()

# Ruta para editar un registro de Oficina Actuante
@app.route('/editar_oficina_actuante', methods=['POST'])
def editar_oficina_actuante():
    if request.method == 'POST':
        id = request.form['editId']
        nuevo_nombre = request.form['nuevo_nombre']
        actualizar_oficina_actuante(id, nuevo_nombre)
        return redirect(url_for('oficinas_actuantes'))

    return 'Registro de Oficina Actuante editado con éxito'

# Función para actualizar un registro de Oficina Actuante en la base de datos
def actualizar_oficina_actuante(id, nuevo_nombre):
    conn = sqlite3.connect('oficinas_actuantes.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE oficinas_actuantes SET nombre = ? WHERE id = ?', (nuevo_nombre, id))
    conn.commit()
    conn.close()

# Función para obtener registros de Oficinas Actuantes desde la base de datos
def obtener_oficinas_actuantes():
    conn = sqlite3.connect('oficinas_actuantes.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM oficinas_actuantes')
    oficinas_actuantes = cursor.fetchall()
    conn.close()
    return oficinas_actuantes

# Ruta para eliminar un registro de Oficina Actuante
@app.route('/eliminar_oficina_actuante/<int:oficina_actuante_id>', methods=['POST'])
def eliminar_oficina_actuante(oficina_actuante_id):
    if request.method == 'POST':
        try:
            # Obtener una conexión a la base de datos de Oficinas Actuantes
            conn_oficinas_actuantes = sqlite3.connect('oficinas_actuantes.db')
            cursor = conn_oficinas_actuantes.cursor()

            # Construir la consulta SQL para eliminar la Oficina Actuante por su ID
            query = 'DELETE FROM oficinas_actuantes WHERE id = ?'
            cursor.execute(query, (oficina_actuante_id,))

            # Aplicar el cambio en la base de datos
            conn_oficinas_actuantes.commit()
            conn_oficinas_actuantes.close()

            return "Registro eliminado correctamente"  # O puedes redirigir a otra página si lo prefieres
        except sqlite3.Error as e:
            print("Error al eliminar el registro de Oficina Actuante:", e)
            return "Error al eliminar el registro de Oficina Actuante.", 500
    else:
        # Maneja solicitudes GET si es necesario, por ejemplo, mostrando una página de confirmación
        return render_template('eliminar_oficina_actuante.html', oficina_actuante_id=oficina_actuante_id)


# Función para crear la tabla de Personal Policial del PNR si no existe
def crear_tabla_personal_policial_pnr():
    conn = sqlite3.connect('personal_policial_pnr.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS personal_policial_pnr (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Llama a esta función para crear la tabla si no existe
crear_tabla_personal_policial_pnr()

# Ruta principal para Personal Policial del PNR
@app.route('/parametricas/personal_policial_pnr')
def personal_policial_pnr():
    # Obtener registros de la base de datos
    registros = obtener_personal_policial_pnr()
    
    # Renderizar la plantilla HTML y pasar los registros como contexto
    return render_template('personal_policial_pnr.html', registros=registros)

# Ruta para guardar un nuevo registro de Personal Policial del PNR
@app.route('/guardar_personal_policial_pnr', methods=['POST'])
def guardar_personal_policial_pnr():
    if request.method == 'POST':
        nombre = request.form['nombre']  # Obtén el nombre del formulario
        crear_personal_policial_pnr(nombre)  # Llama a la función para crear un registro
        return redirect('/parametricas/personal_policial_pnr')  # Redirige a la página de Personal Policial del PNR

    return 'Registro de Personal Policial del PNR guardado con éxito'

# Función para crear un nuevo registro de Personal Policial del PNR en la base de datos
def crear_personal_policial_pnr(nombre):
    conn = sqlite3.connect('personal_policial_pnr.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO personal_policial_pnr (nombre) VALUES (?)', (nombre,))
    conn.commit()
    conn.close()

# Ruta para editar un registro de Personal Policial del PNR
@app.route('/editar_personal_policial_pnr', methods=['POST'])
def editar_personal_policial_pnr():
    if request.method == 'POST':
        id = request.form['editId']
        nuevo_nombre = request.form['nuevo_nombre']
        actualizar_personal_policial_pnr(id, nuevo_nombre)
        return redirect(url_for('personal_policial_pnr'))

    return 'Registro de Personal Policial del PNR editado con éxito'

# Función para actualizar un registro de Personal Policial del PNR en la base de datos
def actualizar_personal_policial_pnr(id, nuevo_nombre):
    conn = sqlite3.connect('personal_policial_pnr.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE personal_policial_pnr SET nombre = ? WHERE id = ?', (nuevo_nombre, id))
    conn.commit()
    conn.close()

# Función para obtener registros de Personal Policial del PNR desde la base de datos
def obtener_personal_policial_pnr():
    conn = sqlite3.connect('personal_policial_pnr.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM personal_policial_pnr')
    personal_policial_pnr = cursor.fetchall()
    conn.close()
    return personal_policial_pnr

# Ruta para eliminar un registro de Personal Policial del PNR
@app.route('/eliminar_personal_policial_pnr/<int:personal_policial_pnr_id>', methods=['POST'])
def eliminar_personal_policial_pnr(personal_policial_pnr_id):
    if request.method == 'POST':
        try:
            # Obtener una conexión a la base de datos de Personal Policial del PNR
            conn_personal_policial_pnr = sqlite3.connect('personal_policial_pnr.db')
            cursor = conn_personal_policial_pnr.cursor()

            # Construir la consulta SQL para eliminar el Personal Policial del PNR por su ID
            query = 'DELETE FROM personal_policial_pnr WHERE id = ?'
            cursor.execute(query, (personal_policial_pnr_id,))

            # Aplicar el cambio en la base de datos
            conn_personal_policial_pnr.commit()
            conn_personal_policial_pnr.close()

            return "Registro eliminado correctamente"  # O puedes redirigir a otra página si lo prefieres
        except sqlite3.Error as e:
            print("Error al eliminar el registro de Personal Policial del PNR:", e)
            return "Error al eliminar el registro de Personal Policial del PNR.", 500
    else:
        # Maneja solicitudes GET si es necesario, por ejemplo, mostrando una página de confirmación
        return render_template('eliminar_personal_policial_pnr.html', personal_policial_pnr_id=personal_policial_pnr_id)


# Función para crear la tabla de Puntos Focales si no existe
def crear_tabla_puntos_focales():
    conn = sqlite3.connect('puntos_focales.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS puntos_focales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Llama a esta función para crear la tabla si no existe
crear_tabla_puntos_focales()

# Ruta principal para Puntos Focales
@app.route('/parametricas/puntos_focales')
def puntos_focales():
    # Obtener registros de la base de datos
    registros = obtener_puntos_focales()
    
    # Renderizar la plantilla HTML y pasar los registros como contexto
    return render_template('puntos_focales.html', registros=registros)

# Ruta para guardar un nuevo registro de Punto Focal
@app.route('/guardar_punto_focal', methods=['POST'])
def guardar_punto_focal():
    if request.method == 'POST':
        nombre = request.form['nombre']  # Obtén el nombre del formulario
        crear_punto_focal(nombre)  # Llama a la función para crear un registro
        return redirect('/parametricas/puntos_focales')  # Redirige a la página de Puntos Focales

    return 'Registro de Punto Focal guardado con éxito'

# Función para crear un nuevo registro de Punto Focal en la base de datos
def crear_punto_focal(nombre):
    conn = sqlite3.connect('puntos_focales.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO puntos_focales (nombre) VALUES (?)', (nombre,))
    conn.commit()
    conn.close()

# Ruta para editar un registro de Punto Focal
@app.route('/editar_punto_focal', methods=['POST'])
def editar_punto_focal():
    if request.method == 'POST':
        id = request.form['editId']
        nuevo_nombre = request.form['nuevo_nombre']
        actualizar_punto_focal(id, nuevo_nombre)
        return redirect(url_for('puntos_focales'))

    return 'Registro de Punto Focal editado con éxito'

# Función para actualizar un registro de Punto Focal en la base de datos
def actualizar_punto_focal(id, nuevo_nombre):
    conn = sqlite3.connect('puntos_focales.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE puntos_focales SET nombre = ? WHERE id = ?', (nuevo_nombre, id))
    conn.commit()
    conn.close()

# Función para obtener registros de Puntos Focales desde la base de datos
def obtener_puntos_focales():
    conn = sqlite3.connect('puntos_focales.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM puntos_focales')
    puntos_focales = cursor.fetchall()
    conn.close()
    return puntos_focales

# Ruta para eliminar un registro de Punto Focal
@app.route('/eliminar_punto_focal/<int:punto_focal_id>', methods=['POST'])
def eliminar_punto_focal(punto_focal_id):
    if request.method == 'POST':
        try:
            # Obtener una conexión a la base de datos de Punto Focal
            conn_punto_focal = sqlite3.connect('puntos_focales.db')
            cursor = conn_punto_focal.cursor()

            # Construir la consulta SQL para eliminar el Punto Focal por su ID
            query = 'DELETE FROM puntos_focales WHERE id = ?'
            cursor.execute(query, (punto_focal_id,))

            # Aplicar el cambio en la base de datos
            conn_punto_focal.commit()
            conn_punto_focal.close()

            return "Registro eliminado correctamente"  # O puedes redirigir a otra página si lo prefieres
        except sqlite3.Error as e:
            print("Error al eliminar el registro de Punto Focal:", e)
            return "Error al eliminar el registro de Punto Focal.", 500
    else:
        # Maneja solicitudes GET si es necesario, por ejemplo, mostrando una página de confirmación
        return render_template('eliminar_punto_focal.html', punto_focal_id=punto_focal_id)


# Función para crear la tabla de Reservas si no existe
def crear_tabla_reservas():
    conn = sqlite3.connect('reservas.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Llama a esta función para crear la tabla si no existe
crear_tabla_reservas()

# Ruta principal para Reservas
@app.route('/parametricas/reservas')
def reservas():
    # Obtener registros de la base de datos
    registros = obtener_reservas()
    
    # Renderizar la plantilla HTML y pasar los registros como contexto
    return render_template('reservas.html', registros=registros)

# Ruta para guardar un nuevo registro de Reserva
@app.route('/guardar_reserva', methods=['POST'])
def guardar_reserva():
    if request.method == 'POST':
        nombre = request.form['nombre']  # Obtén el nombre del formulario
        crear_reserva(nombre)  # Llama a la función para crear un registro
        return redirect('/parametricas/reservas')  # Redirige a la página de Reservas

    return 'Registro de Reserva guardado con éxito'

# Función para crear un nuevo registro de Reserva en la base de datos
def crear_reserva(nombre):
    conn = sqlite3.connect('reservas.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO reservas (nombre) VALUES (?)', (nombre,))
    conn.commit()
    conn.close()

# Ruta para editar un registro de Reserva
@app.route('/editar_reserva', methods=['POST'])
def editar_reserva():
    if request.method == 'POST':
        id = request.form['editId']
        nuevo_nombre = request.form['nuevo_nombre']
        actualizar_reserva(id, nuevo_nombre)
        return redirect(url_for('reservas'))

    return 'Registro de Reserva editado con éxito'

# Función para actualizar un registro de Reserva en la base de datos
def actualizar_reserva(id, nuevo_nombre):
    conn = sqlite3.connect('reservas.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE reservas SET nombre = ? WHERE id = ?', (nuevo_nombre, id))
    conn.commit()
    conn.close()

# Función para obtener registros de Reservas desde la base de datos
def obtener_reservas():
    conn = sqlite3.connect('reservas.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reservas')
    reservas = cursor.fetchall()
    conn.close()
    return reservas

# Ruta para eliminar un registro de Reserva
@app.route('/eliminar_reserva/<int:reserva_id>', methods=['POST'])
def eliminar_reserva(reserva_id):
    if request.method == 'POST':
        try:
            # Obtener una conexión a la base de datos de Reserva
            conn_reserva = sqlite3.connect('reservas.db')
            cursor = conn_reserva.cursor()

            # Construir la consulta SQL para eliminar la Reserva por su ID
            query = 'DELETE FROM reservas WHERE id = ?'
            cursor.execute(query, (reserva_id,))

            # Aplicar el cambio en la base de datos
            conn_reserva.commit()
            conn_reserva.close()

            return "Registro eliminado correctamente"  # O puedes redirigir a otra página si lo prefieres
        except sqlite3.Error as e:
            print("Error al eliminar el registro de Reserva:", e)
            return "Error al eliminar el registro de Reserva.", 500
    else:
        # Maneja solicitudes GET si es necesario, por ejemplo, mostrando una página de confirmación
        return render_template('eliminar_reserva.html', reserva_id=reserva_id)


# Función para crear la tabla de Roles de Personas si no existe
def crear_tabla_roles_personas():
    conn = sqlite3.connect('roles_personas.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roles_personas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Llama a esta función para crear la tabla si no existe
crear_tabla_roles_personas()

# Ruta principal para Roles de Personas
@app.route('/parametricas/roles_personas')
def roles_personas():
    # Obtener registros de la base de datos
    registros = obtener_roles_personas()
    
    # Renderizar la plantilla HTML y pasar los registros como contexto
    return render_template('roles_personas.html', registros=registros)

# Ruta para guardar un nuevo registro de Rol de Persona
@app.route('/guardar_rol_persona', methods=['POST'])
def guardar_rol_persona():
    if request.method == 'POST':
        nombre = request.form['nombre']  # Obtén el nombre del formulario
        crear_rol_persona(nombre)  # Llama a la función para crear un registro
        return redirect('/parametricas/roles_personas')  # Redirige a la página de Roles de Personas

    return 'Registro de Rol de Persona guardado con éxito'

# Función para crear un nuevo registro de Rol de Persona en la base de datos
def crear_rol_persona(nombre):
    conn = sqlite3.connect('roles_personas.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO roles_personas (nombre) VALUES (?)', (nombre,))
    conn.commit()
    conn.close()

# Ruta para editar un registro de Rol de Persona
@app.route('/editar_rol_persona', methods=['POST'])
def editar_rol_persona():
    if request.method == 'POST':
        id = request.form['editId']
        nuevo_nombre = request.form['nuevo_nombre']
        actualizar_rol_persona(id, nuevo_nombre)
        return redirect(url_for('roles_personas'))

    return 'Registro de Rol de Persona editado con éxito'

# Función para actualizar un registro de Rol de Persona en la base de datos
def actualizar_rol_persona(id, nuevo_nombre):
    conn = sqlite3.connect('roles_personas.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE roles_personas SET nombre = ? WHERE id = ?', (nuevo_nombre, id))
    conn.commit()
    conn.close()

# Función para obtener registros de Roles de Personas desde la base de datos
def obtener_roles_personas():
    conn = sqlite3.connect('roles_personas.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM roles_personas')
    roles_personas = cursor.fetchall()
    conn.close()
    return roles_personas

# Ruta para eliminar un registro de Rol de Persona
@app.route('/eliminar_rol_persona/<int:rol_persona_id>', methods=['POST'])
def eliminar_rol_persona(rol_persona_id):
    if request.method == 'POST':
        try:
            # Obtener una conexión a la base de datos de Rol de Persona
            conn_rol_persona = sqlite3.connect('roles_personas.db')
            cursor = conn_rol_persona.cursor()

            # Construir la consulta SQL para eliminar el Rol de Persona por su ID
            query = 'DELETE FROM roles_personas WHERE id = ?'
            cursor.execute(query, (rol_persona_id,))

            # Aplicar el cambio en la base de datos
            conn_rol_persona.commit()
            conn_rol_persona.close()

            return "Registro eliminado correctamente"  # O puedes redirigir a otra página si lo prefieres
        except sqlite3.Error as e:
            print("Error al eliminar el registro de Rol de Persona:", e)
            return "Error al eliminar el registro de Rol de Persona.", 500
    else:
        # Maneja solicitudes GET si es necesario, por ejemplo, mostrando una página de confirmación
        return render_template('eliminar_rol_persona.html', rol_persona_id=rol_persona_id)


# Función para crear la tabla de Tipos de Intervenciones si no existe
def crear_tabla_tipos_intervenciones():
    conn = sqlite3.connect('tipos_intervenciones.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tipos_intervenciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Llama a esta función para crear la tabla si no existe
crear_tabla_tipos_intervenciones()

# Ruta principal para Tipos de Intervenciones
@app.route('/parametricas/tipos_intervenciones')
def tipos_intervenciones():
    # Obtener registros de la base de datos
    registros = obtener_tipos_intervenciones()
    
    # Renderizar la plantilla HTML y pasar los registros como contexto
    return render_template('tipos_intervenciones.html', registros=registros)

# Ruta para guardar un nuevo registro de Tipo de Intervención
@app.route('/guardar_tipo_intervencion', methods=['POST'])
def guardar_tipo_intervencion():
    if request.method == 'POST':
        nombre = request.form['nombre']  # Obtén el nombre del formulario
        crear_tipo_intervencion(nombre)  # Llama a la función para crear un registro
        return redirect('/parametricas/tipos_intervenciones')  # Redirige a la página de Tipos de Intervenciones

    return 'Registro de Tipo de Intervención guardado con éxito'

# Función para crear un nuevo registro de Tipo de Intervención en la base de datos
def crear_tipo_intervencion(nombre):
    conn = sqlite3.connect('tipos_intervenciones.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tipos_intervenciones (nombre) VALUES (?)', (nombre,))
    conn.commit()
    conn.close()

# Ruta para editar un registro de Tipo de Intervención
@app.route('/editar_tipo_intervencion', methods=['POST'])
def editar_tipo_intervencion():
    if request.method == 'POST':
        id = request.form['editId']
        nuevo_nombre = request.form['nuevo_nombre']
        actualizar_tipo_intervencion(id, nuevo_nombre)
        return redirect(url_for('tipos_intervenciones'))

    return 'Registro de Tipo de Intervención editado con éxito'

# Función para actualizar un registro de Tipo de Intervención en la base de datos
def actualizar_tipo_intervencion(id, nuevo_nombre):
    conn = sqlite3.connect('tipos_intervenciones.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE tipos_intervenciones SET nombre = ? WHERE id = ?', (nuevo_nombre, id))
    conn.commit()
    conn.close()

# Función para obtener registros de Tipos de Intervenciones desde la base de datos
def obtener_tipos_intervenciones():
    conn = sqlite3.connect('tipos_intervenciones.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tipos_intervenciones')
    tipos_intervenciones = cursor.fetchall()
    conn.close()
    return tipos_intervenciones

# Ruta para eliminar un registro de Tipo de Intervención
@app.route('/eliminar_tipo_intervencion/<int:tipo_intervencion_id>', methods=['POST'])
def eliminar_tipo_intervencion(tipo_intervencion_id):
    if request.method == 'POST':
        try:
            # Obtener una conexión a la base de datos de Tipo de Intervención
            conn_tipo_intervencion = sqlite3.connect('tipos_intervenciones.db')
            cursor = conn_tipo_intervencion.cursor()

            # Construir la consulta SQL para eliminar el Tipo de Intervención por su ID
            query = 'DELETE FROM tipos_intervenciones WHERE id = ?'
            cursor.execute(query, (tipo_intervencion_id,))

            # Aplicar el cambio en la base de datos
            conn_tipo_intervencion.commit()
            conn_tipo_intervencion.close()

            return "Registro eliminado correctamente"  # O puedes redirigir a otra página si lo prefieres
        except sqlite3.Error as e:
            print("Error al eliminar el registro de Tipo de Intervención:", e)
            return "Error al eliminar el registro de Tipo de Intervención.", 500
    else:
        # Maneja solicitudes GET si es necesario, por ejemplo, mostrando una página de confirmación
        return render_template('eliminar_tipo_intervencion.html', tipo_intervencion_id=tipo_intervencion_id)


# Función para crear la tabla de Tipos de Articulaciones si no existe
def crear_tabla_tipos_articulaciones():
    conn = sqlite3.connect('tipos_articulaciones.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tipos_articulaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Llama a esta función para crear la tabla si no existe
crear_tabla_tipos_articulaciones()

# Ruta principal para Tipos de Articulaciones
@app.route('/parametricas/tipos_articulaciones')
def tipos_articulaciones():
    # Obtener registros de la base de datos
    registros = obtener_tipos_articulaciones()
    
    # Renderizar la plantilla HTML y pasar los registros como contexto
    return render_template('tipos_articulaciones.html', registros=registros)

# Ruta para guardar un nuevo registro de Tipo de Articulación
@app.route('/guardar_tipo_articulacion', methods=['POST'])
def guardar_tipo_articulacion():
    if request.method == 'POST':
        nombre = request.form['nombre']  # Obtén el nombre del formulario
        crear_tipo_articulacion(nombre)  # Llama a la función para crear un registro
        return redirect('/parametricas/tipos_articulaciones')  # Redirige a la página de Tipos de Articulaciones

    return 'Registro de Tipo de Articulación guardado con éxito'

# Función para crear un nuevo registro de Tipo de Articulación en la base de datos
def crear_tipo_articulacion(nombre):
    conn = sqlite3.connect('tipos_articulaciones.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tipos_articulaciones (nombre) VALUES (?)', (nombre,))
    conn.commit()
    conn.close()

# Ruta para editar un registro de Tipo de Articulación
@app.route('/editar_tipo_articulacion', methods=['POST'])
def editar_tipo_articulacion():
    if request.method == 'POST':
        id = request.form['editId']
        nuevo_nombre = request.form['nuevo_nombre']
        actualizar_tipo_articulacion(id, nuevo_nombre)
        return redirect(url_for('tipos_articulaciones'))

    return 'Registro de Tipo de Articulación editado con éxito'

# Función para actualizar un registro de Tipo de Articulación en la base de datos
def actualizar_tipo_articulacion(id, nuevo_nombre):
    conn = sqlite3.connect('tipos_articulaciones.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE tipos_articulaciones SET nombre = ? WHERE id = ?', (nuevo_nombre, id))
    conn.commit()
    conn.close()

# Función para obtener registros de Tipos de Articulaciones desde la base de datos
def obtener_tipos_articulaciones():
    conn = sqlite3.connect('tipos_articulaciones.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tipos_articulaciones')
    tipos_articulaciones = cursor.fetchall()
    conn.close()
    return tipos_articulaciones

# Ruta para eliminar un registro de Tipo de Articulación
@app.route('/eliminar_tipo_articulacion/<int:tipo_articulacion_id>', methods=['POST'])
def eliminar_tipo_articulacion(tipo_articulacion_id):
    if request.method == 'POST':
        try:
            # Obtener una conexión a la base de datos de Tipo de Articulación
            conn_tipo_articulacion = sqlite3.connect('tipos_articulaciones.db')
            cursor = conn_tipo_articulacion.cursor()

            # Construir la consulta SQL para eliminar el Tipo de Articulación por su ID
            query = 'DELETE FROM tipos_articulaciones WHERE id = ?'
            cursor.execute(query, (tipo_articulacion_id,))

            # Aplicar el cambio en la base de datos
            conn_tipo_articulacion.commit()
            conn_tipo_articulacion.close()

            return "Registro eliminado correctamente"  # O puedes redirigir a otra página si lo prefieres
        except sqlite3.Error as e:
            print("Error al eliminar el registro de Tipo de Articulación:", e)
            return "Error al eliminar el registro de Tipo de Articulación.", 500
    else:
        # Maneja solicitudes GET si es necesario, por ejemplo, mostrando una página de confirmación
        return render_template('eliminar_tipo_articulacion.html', tipo_articulacion_id=tipo_articulacion_id)


# Función para crear la tabla de Tipos de Documentos si no existe
@app.route('/parametricas/tipos_documentos')
def tipos_documentos():
    # Obtener registros de la base de datos
    registros = obtener_tipos_documentos()
    
    # Renderizar la plantilla HTML y pasar los registros como contexto
    return render_template('tipos_documentos.html', registros=registros)

# Ruta para guardar un nuevo registro de Tipo de Documento
@app.route('/guardar_tipo_documento', methods=['POST'])
def guardar_tipo_documento():
    if request.method == 'POST':
        nombre = request.form['nombre']  # Obtén el nombre del formulario
        crear_tipo_documento(nombre)  # Llama a la función para crear un registro
        return redirect('/parametricas/tipos_documentos')  # Redirige a la página de Tipos de Documentos

    return 'Registro de Tipo de Documento guardado con éxito'

# Función para crear un nuevo registro de Tipo de Documento en la base de datos
def crear_tipo_documento(nombre):
    conn = sqlite3.connect('tipos_documentos.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tipos_documentos (nombre) VALUES (?)', (nombre,))
    conn.commit()
    conn.close()

# Ruta para editar un registro de Tipo de Documento
@app.route('/editar_tipo_documento', methods=['POST'])
def editar_tipo_documento():
    if request.method == 'POST':
        id = request.form['editId']
        nuevo_nombre = request.form['nuevo_nombre']
        actualizar_tipo_documento(id, nuevo_nombre)
        return redirect(url_for('tipos_documentos'))

    return 'Registro de Tipo de Documento editado con éxito'

# Función para actualizar un registro de Tipo de Documento en la base de datos
def actualizar_tipo_documento(id, nuevo_nombre):
    conn = sqlite3.connect('tipos_documentos.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE tipos_documentos SET nombre = ? WHERE id = ?', (nuevo_nombre, id))
    conn.commit()
    conn.close()

# Función para obtener registros de Tipos de Documentos desde la base de datos
def obtener_tipos_documentos():
    conn_tipos_documentos = sqlite3.connect('tipos_documentos.db')
    cursor = conn_tipos_documentos.cursor()
    cursor.execute('SELECT nombre FROM tipos_documentos')
    tipos_documentos = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn_tipos_documentos.close()
    return tipos_documentos

# Ruta para eliminar un registro de Tipo de Documento
@app.route('/eliminar_tipo_documento/<int:tipo_documento_id>', methods=['POST'])
def eliminar_tipo_documento(tipo_documento_id):
    if request.method == 'POST':
        try:
            # Obtener una conexión a la base de datos de Tipo de Documento
            conn_tipo_documento = sqlite3.connect('tipos_documentos.db')
            cursor = conn_tipo_documento.cursor()

            # Construir la consulta SQL para eliminar el Tipo de Documento por su ID
            query = 'DELETE FROM tipos_documentos WHERE id = ?'
            cursor.execute(query, (tipo_documento_id,))

            # Aplicar el cambio en la base de datos
            conn_tipo_documento.commit()
            conn_tipo_documento.close()

            return "Registro eliminado correctamente"  # O puedes redirigir a otra página si lo prefieres
        except sqlite3.Error as e:
            print("Error al eliminar el registro de Tipo de Documento:", e)
            return "Error al eliminar el registro de Tipo de Documento.", 500
    else:
        # Maneja solicitudes GET si es necesario, por ejemplo, mostrando una página de confirmación
        return render_template('eliminar_tipo_documento.html', tipo_documento_id=tipo_documento_id)



# Función para crear la tabla de Tipologías si no existe
def crear_tabla_tipologias():
    conn = sqlite3.connect('tipologias.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tipologias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Llama a esta función para crear la tabla si no existe
crear_tabla_tipologias()

# Ruta principal para Tipologías
@app.route('/parametricas/tipologias')
def tipologias():
    # Obtener registros de la base de datos
    registros = obtener_tipologias()
    
    # Renderizar la plantilla HTML y pasar los registros como contexto
    return render_template('tipologias.html', registros=registros)

# Ruta para guardar un nuevo registro de Tipología
@app.route('/guardar_tipologia', methods=['POST'])
def guardar_tipologia():
    if request.method == 'POST':
        nombre = request.form['nombre']  # Obtén el nombre del formulario
        crear_tipologia(nombre)  # Llama a la función para crear un registro
        return redirect('/parametricas/tipologias')  # Redirige a la página de Tipologías

    return 'Registro de Tipología guardado con éxito'

# Función para crear un nuevo registro de Tipología en la base de datos
def crear_tipologia(nombre):
    conn = sqlite3.connect('tipologias.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tipologias (nombre) VALUES (?)', (nombre,))
    conn.commit()
    conn.close()

# Ruta para editar un registro de Tipología
@app.route('/editar_tipologia', methods=['POST'])
def editar_tipologia():
    if request.method == 'POST':
        id = request.form['editId']
        nuevo_nombre = request.form['nuevo_nombre']
        actualizar_tipologia(id, nuevo_nombre)
        return redirect(url_for('tipologias'))

    return 'Registro de Tipología editado con éxito'

# Función para actualizar un registro de Tipología en la base de datos
def actualizar_tipologia(id, nuevo_nombre):
    conn = sqlite3.connect('tipologias.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE tipologias SET nombre = ? WHERE id = ?', (nuevo_nombre, id))
    conn.commit()
    conn.close()

# Función para obtener registros de Tipologías desde la base de datos
def obtener_tipologias():
    conn = sqlite3.connect('tipologias.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tipologias')
    tipologias = cursor.fetchall()
    conn.close()
    return tipologias

# Ruta para eliminar un registro de Tipología
@app.route('/eliminar_tipologia/<int:tipologia_id>', methods=['POST'])
def eliminar_tipologia(tipologia_id):
    if request.method == 'POST':
        try:
            # Obtener una conexión a la base de datos de Tipología
            conn_tipologia = sqlite3.connect('tipologias.db')
            cursor = conn_tipologia.cursor()

            # Construir la consulta SQL para eliminar la Tipología por su ID
            query = 'DELETE FROM tipologias WHERE id = ?'
            cursor.execute(query, (tipologia_id,))

            # Aplicar el cambio en la base de datos
            conn_tipologia.commit()
            conn_tipologia.close()

            return "Registro eliminado correctamente"  # O puedes redirigir a otra página si lo prefieres
        except sqlite3.Error as e:
            print("Error al eliminar el registro de Tipología:", e)
            return "Error al eliminar el registro de Tipología.", 500
    else:
        # Maneja solicitudes GET si es necesario, por ejemplo, mostrando una página de confirmación
        return render_template('eliminar_tipologia.html', tipologia_id=tipologia_id)

# Función para crear la tabla de Roles si no existe
def crear_tabla_roles():
    conn = sqlite3.connect('roles.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            apellido_nombre TEXT NOT NULL,
            rol TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Llama a esta función para crear la tabla si no existe
crear_tabla_roles()

# Ruta principal para Roles
@app.route('/parametricas/roles')
def roles():
    # Obtener registros de la base de datos
    registros = obtener_roles()
    
    # Renderizar la plantilla HTML y pasar los registros como contexto
    return render_template('roles.html', registros=registros)

# Ruta para crear un nuevo registro de Rol
@app.route('/guardar_rol', methods=['POST'])
def guardar_rol():
    if request.method == 'POST':
        apellido_nombre = request.form['apellido_nombre']
        rol = request.form['rol']
        crear_rol(apellido_nombre, rol)
        return redirect('/parametricas/roles')
    return 'Registro de Rol guardado con éxito'

# Función para crear un nuevo registro de Rol en la base de datos
def crear_rol(apellido_nombre, rol):
    conn = sqlite3.connect('roles.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO roles (apellido_nombre, rol) VALUES (?, ?)', (apellido_nombre, rol))
    conn.commit()
    conn.close()

# Ruta para editar un registro de Rol
@app.route('/editar_rol', methods=['POST'])
def editar_rol():
    if request.method == 'POST':
        id = request.form['editId']
        nuevo_rol = request.form['nuevo_rol']
        actualizar_rol(id, nuevo_rol)
        return redirect('/parametricas/roles')
    return 'Registro de Rol editado con éxito'

# Función para actualizar un registro de Rol en la base de datos
def actualizar_rol(id, nuevo_rol):
    conn = sqlite3.connect('roles.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE roles SET rol = ? WHERE id = ?', (nuevo_rol, id))
    conn.commit()
    conn.close()

# Ruta para eliminar un registro de Rol
@app.route('/eliminar_rol/<int:id>', methods=['POST'])
def eliminar_rol(id):
    if request.method == 'POST':
        try:
            # Obtener una conexión a la base de datos de Rol
            conn_rol = sqlite3.connect('roles.db')
            cursor = conn_rol.cursor()

            # Construir la consulta SQL para eliminar el rol por su ID
            query = 'DELETE FROM roles WHERE id = ?'
            cursor.execute(query, (id,))

            # Aplicar el cambio en la base de datos
            conn_rol.commit()
            conn_rol.close()

            return "Rol eliminado correctamente"  # O puedes redirigir a otra página si lo prefieres
        except sqlite3.Error as e:
            print("Error al eliminar el rol:", e)
            return "Error al eliminar el rol.", 500

    return "Método no permitido", 405

# Función para obtener registros de Roles desde la base de datos
def obtener_roles():
    conn = sqlite3.connect('roles.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM roles')
    roles = cursor.fetchall()
    conn.close()
    return roles

if __name__ == '__main__':
    app.run(debug=True)
