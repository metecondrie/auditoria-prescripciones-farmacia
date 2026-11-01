CREATE TABLE dim_pacientes (
    id_paciente INT PRIMARY KEY,
    hash_identidad VARCHAR(255) NOT NULL,
    fecha_nacimiento DATE,
    genero VARCHAR(50)
);

CREATE TABLE dim_medicos (
    id_medico INT PRIMARY KEY,
    matricula_hash VARCHAR(255) NOT NULL,
    especialidad VARCHAR(100),
    valido_desde DATE,
    valido_hasta DATE,
    es_actual BOOLEAN
);

CREATE TABLE dim_medicamentos (
    id_medicamento SERIAL PRIMARY KEY,
    codigo_fda VARCHAR(100) NOT NULL UNIQUE,
    principio_activo VARCHAR(255),
    nivel_riesgo INT CHECK (nivel_riesgo BETWEEN 1 AND 5)
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
    id_paciente INT NOT NULL REFERENCES dim_pacientes(id_paciente),
    id_medico INT NOT NULL REFERENCES dim_medicos(id_medico),
    id_medicamento INT NOT NULL REFERENCES dim_medicamentos(id_medicamento),
    fecha_prescripcion DATE NOT NULL REFERENCES dim_calendario(fecha),
    dosis_mg INT NOT NULL CHECK (dosis_mg > 0),
    cantidad_cajas INT NOT NULL CHECK (cantidad_cajas > 0)
);