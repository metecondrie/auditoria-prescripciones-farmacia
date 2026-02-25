CREATE TABLE dim_pacientes (
    id_paciente SERIAL PRIMARY KEY,
    hash_identidad VARCHAR(255) NOT NULL,
    fecha_nacimiento DATE,
    genero VARCHAR(50)
);

CREATE TABLE dim_medicos (
    id_medico SERIAL PRIMARY KEY,
    matricula_hash VARCHAR(255) NOT NULL,
    especialidad VARCHAR(100),
    valido_desde DATE,
    valido_hasta DATE,
    es_actual BOOLEAN
);

CREATE TABLE dim_medicamentos (
    id_medicamento SERIAL PRIMARY KEY,
    codigo_fda VARCHAR(100) NOT NULL,
    principio_activo VARCHAR(255),
    nivel_riesgo INT
);

CREATE TABLE dim_calendario (
    fecha DATE PRIMARY KEY,
    anio INT,
    mes INT,
    dia_semana INT,
    es_feriado BOOLEAN
);

CREATE TABLE fact_prescripciones (
    id_prescripcion_linea SERIAL PRIMARY KEY,
    id_paciente INT REFERENCES dim_pacientes(id_paciente),
    id_medico INT REFERENCES dim_medicos(id_medico),
    id_medicamento INT REFERENCES dim_medicamentos(id_medicamento),
    fecha_prescripcion DATE REFERENCES dim_calendario(fecha),
    dosis_mg INT,
    cantidad_cajas INT
);