-- Educational rules only: 800 mg is a generator-specific boundary, NOT a
-- safe/unsafe dose, clinical indication, or adverse-event classification.
-- Grain: one row per prescription line. Joins cannot multiply rows because
-- every foreign key references a primary/unique key.

CREATE OR REPLACE VIEW vw_auditoria_prescripciones AS
SELECT
    p.*,
    m.codigo_fda,
    m.principio_activo,
    d.especialidad,
    (p.dosis_mg > 800) AS es_anomalia_demo
FROM fact_prescripciones AS p
JOIN dim_medicamentos AS m USING (id_medicamento)
JOIN dim_medicos AS d USING (id_medico);

-- Detail for drill-through; NEVER use this filtered view as the denominator.
CREATE OR REPLACE VIEW vw_auditoria_anomalias AS
SELECT *
FROM vw_auditoria_prescripciones
WHERE es_anomalia_demo;

-- Empty inputs: percentage is NULL (not a fabricated zero percent).
CREATE OR REPLACE VIEW vw_resumen_auditoria AS
SELECT
    COUNT(*) AS total_prescripciones,
    COUNT(*) FILTER (WHERE es_anomalia_demo) AS anomalias,
    100.0 * COUNT(*) FILTER (WHERE es_anomalia_demo)
          / NULLIF(COUNT(*), 0) AS porcentaje_anomalias
FROM vw_auditoria_prescripciones;

-- Complete denominators PER medication. Use rates, not only counts,
-- when comparing products with different volumes.
CREATE OR REPLACE VIEW vw_resumen_por_medicamento AS
SELECT
    id_medicamento,
    codigo_fda,
    principio_activo,
    COUNT(*) AS total_prescripciones,
    COUNT(*) FILTER (WHERE es_anomalia_demo) AS anomalias,
    100.0 * COUNT(*) FILTER (WHERE es_anomalia_demo)
          / NULLIF(COUNT(*), 0) AS porcentaje_anomalias
FROM vw_auditoria_prescripciones
GROUP BY id_medicamento, codigo_fda, principio_activo;

-- One synthetic physician has exactly one specialty (not SCD Type 2).
CREATE OR REPLACE VIEW vw_resumen_por_especialidad AS
SELECT
    especialidad,
    COUNT(*) AS total_prescripciones,
    COUNT(*) FILTER (WHERE es_anomalia_demo) AS anomalias,
    100.0 * COUNT(*) FILTER (WHERE es_anomalia_demo)
          / NULLIF(COUNT(*), 0) AS porcentaje_anomalias
FROM vw_auditoria_prescripciones
GROUP BY especialidad;
