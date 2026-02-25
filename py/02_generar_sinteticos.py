import pandas as pd
from sqlalchemy import create_engine
from faker import Faker
import random
from datetime import datetime, timedelta

# Inicializar Faker con configuración para Argentina
fake = Faker('es_AR')

# 1. Conexión a Postgres
# ¡Cambiá la contraseña si hace falta!
motor_sql = create_engine('postgresql://postgres:alejo265@localhost:5432/auditoria_farmaco')

def generar_datos():
    print("1. Extrayendo IDs de medicamentos reales de la base...")
    df_med = pd.read_sql("SELECT id_medicamento FROM dim_medicamentos", motor_sql)
    lista_medicamentos = df_med['id_medicamento'].tolist()
    
    if not lista_medicamentos:
        print("Error: No hay medicamentos en la base. Ejecutá el script 1 primero.")
        return

    print("2. Generando dim_calendario (2024-2025)...")
    fechas = pd.date_range(start="2024-01-01", end="2025-12-31")
    df_calendario = pd.DataFrame({
        'fecha': fechas.date,
        'anio': fechas.year,
        'mes': fechas.month,
        'dia_semana': fechas.weekday,
        'es_feriado': [random.choice([True, False, False, False]) for _ in fechas]
    })
    df_calendario.to_sql('dim_calendario', motor_sql, if_exists='append', index=False)

    print("3. Generando 5,000 Pacientes...")
    pacientes = []
    for _ in range(5000):
        # Inyectamos 5% de ruido: algunos pacientes no tienen género registrado (None)
        genero = random.choice(['M', 'F', 'X']) if random.random() > 0.05 else None
        pacientes.append({
            'hash_identidad': fake.sha256()[:16], # Simulamos datos enmascarados (Compliance)
            'fecha_nacimiento': fake.date_of_birth(minimum_age=18, maximum_age=90),
            'genero': genero
        })
    df_pacientes = pd.DataFrame(pacientes)
    df_pacientes.to_sql('dim_pacientes', motor_sql, if_exists='append', index=False)

    print("4. Generando 100 Médicos (con historial SCD Tipo 2)...")
    medicos = []
    especialidades = ['Psiquiatría', 'Traumatología', 'Clínica Médica', 'Neurología', 'Oncología']
    for _ in range(100):
        medicos.append({
            'matricula_hash': fake.sha256()[:10],
            'especialidad': random.choice(especialidades),
            'valido_desde': fake.date_between(start_date='-5y', end_date='-1y'),
            'valido_hasta': None, # Si es None, significa que sigue trabajando ahí
            'es_actual': True
        })
    df_medicos = pd.DataFrame(medicos)
    df_medicos.to_sql('dim_medicos', motor_sql, if_exists='append', index=False)

    print("5. Generando 100,000 Prescripciones (La tabla de hechos)...")
    # Para no asfixiar tu i5 y tus 14GB de RAM de golpe, empezamos con 100k filas.
    # Recuperamos los IDs generados por Postgres para mantener la integridad referencial
    df_pac_ids = pd.read_sql("SELECT id_paciente FROM dim_pacientes", motor_sql)['id_paciente'].tolist()
    df_med_ids = pd.read_sql("SELECT id_medico FROM dim_medicos", motor_sql)['id_medico'].tolist()
    lista_fechas = df_calendario['fecha'].tolist()

    prescripciones = []
    for _ in range(100000):
        dosis = random.choice([50, 100, 200, 400, 500, 800])
        
        # INYECCIÓN DE CAOS (Anomalías para detectar en el análisis)
        probabilidad_error = random.random()
        if probabilidad_error < 0.01: 
            dosis = dosis * 100 # Error de tipeo: dosis mortal (ej. 40.000 mg)
            
        prescripciones.append({
            'id_paciente': random.choice(df_pac_ids),
            'id_medico': random.choice(df_med_ids),
            'id_medicamento': random.choice(lista_medicamentos),
            'fecha_prescripcion': random.choice(lista_fechas),
            'dosis_mg': dosis,
            'cantidad_cajas': random.randint(1, 5)
        })
        
    df_presc = pd.DataFrame(prescripciones)
    df_presc.to_sql('fact_prescripciones', motor_sql, if_exists='append', index=False)
    
    print("¡Finalizado! La base de datos ya tiene volumen para analizar.")

if __name__ == '__main__':
    generar_datos()