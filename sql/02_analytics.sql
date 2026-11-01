-- Educational rule matches only the synthetic generator's injected outliers.
CREATE OR REPLACE VIEW vw_auditoria_prescripciones AS
SELECT p.*, m.codigo_fda, m.principio_activo, d.especialidad,
       (p.dosis_mg > 800) AS es_anomalia_demo
FROM fact_prescripciones p
JOIN dim_medicamentos m USING (id_medicamento)
JOIN dim_medicos d USING (id_medico);

CREATE OR REPLACE VIEW vw_auditoria_anomalias AS
SELECT * FROM vw_auditoria_prescripciones WHERE es_anomalia_demo;

CREATE OR REPLACE VIEW vw_resumen_auditoria AS
SELECT COUNT(*) AS total_prescripciones,
       COUNT(*) FILTER (WHERE es_anomalia_demo) AS anomalias,
       100.0 * COUNT(*) FILTER (WHERE es_anomalia_demo)
             / NULLIF(COUNT(*), 0) AS porcentaje_anomalias
FROM vw_auditoria_prescripciones;
