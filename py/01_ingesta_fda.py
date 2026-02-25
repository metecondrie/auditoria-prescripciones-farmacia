import requests
import pandas as pd
from sqlalchemy import create_engine
import random

# 1. Configurar la conexión a tu PostgreSQL local
# IMPORTANTE: Cambiá 'tu_usuario' y 'tu_contraseña' por los que usás en pgAdmin
motor_sql = create_engine('postgresql://postgres:alejo265@localhost:5432/auditoria_farmaco')

def obtener_medicamentos_fda():
    print("Conectando a la API de OpenFDA...")
    # Buscamos 100 medicamentos específicos que actúan sobre el sistema nervioso central 
    # (relevante para auditorías de psicofármacos/analgésicos)
    url = 'https://api.fda.gov/drug/ndc.json?limit=100'
    
    respuesta = requests.get(url)
    
    if respuesta.status_code != 200:
        print(f"Fallo crítico. Código HTTP: {respuesta.status_code}")
        print(f"Detalle del servidor: {respuesta.text}")
        return
        
    datos_crudos = respuesta.json()['results']
    lista_medicamentos = []
    
    for item in datos_crudos:
        # Extraemos solo los campos que coinciden con nuestra tabla SQL.
        # Usamos .get() para asignar un valor por defecto si la API devuelve el campo vacío.
        lista_medicamentos.append({
            'codigo_fda': item.get('product_ndc', 'SIN_CODIGO'),
            'principio_activo': item.get('generic_name', 'DESCONOCIDO_O_COMPUESTO')[:250], 
            'nivel_riesgo': random.randint(1, 5) # Asignamos un score de riesgo simulado del 1 al 5
        })
        
    # 2. Transformar la lista a un DataFrame de Pandas
    df_medicamentos = pd.DataFrame(lista_medicamentos)
    
    # 3. Limpieza básica en memoria: eliminar códigos FDA duplicados
    df_medicamentos = df_medicamentos.drop_duplicates(subset=['codigo_fda'])
    
    print(f"Preparando {len(df_medicamentos)} medicamentos únicos para subir...")
    
    # 4. Inyectar los datos en PostgreSQL
    # if_exists='append' suma los datos sin borrar la tabla original.
    # index=False evita que Pandas intente subir la columna de los números de fila.
    try:
        df_medicamentos.to_sql('dim_medicamentos', motor_sql, if_exists='append', index=False)
        print("Éxito: Los medicamentos ya están en tu base de datos.")
    except Exception as e:
        print(f"Error al subir a la base de datos: {e}")

if __name__ == '__main__':
    obtener_medicamentos_fda()