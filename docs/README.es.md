# Auditoría de prescripciones farmacéuticas

[**English README**](../README.md) · [Definiciones de métricas](METRICS.md) · [Controles y seguridad](QUALITY.md)

![Portada del proyecto: ETL, PostgreSQL y BI sobre datos simulados](../assets/portfolio-cover.svg)

**Caso de portfolio de ingeniería de datos y business intelligence.** Integra un catálogo público de productos farmacéuticos, genera prescripciones completamente ficticias, construye un esquema relacional, calcula métricas auditables en SQL y documenta su uso en Power BI.

> **Alcance:** demostración técnica y educativa con datos sintéticos. No es un sistema clínico, no detecta errores reales de prescripción y no permite concluir que una dosis sea segura o peligrosa.

## Resumen ejecutivo

| Competencia | Evidencia |
| --- | --- |
| **Python / ETL** | Ingesta del catálogo openFDA NDC, controles de estructura, snapshot reproducible con SHA-256 y actualización idempotente |
| **Modelado dimensional** | Cuatro dimensiones (pacientes, médicos, medicamentos, calendario) y una tabla de hechos con claves foráneas |
| **Análisis SQL** | Vistas de detalle, anomalías y tasas segmentadas con denominadores correctamente definidos |
| **Calidad de datos** | Semilla fija, cargas transaccionales, restricciones, pruebas de unidad e integración |
| **BI** | Especificación de medidas DAX y orientación para reconstruir un tablero verificable |
| **Comunicación técnica** | Metodología, limitaciones, trazabilidad de resultados y riesgos documentados |

## Resultados reproducibles

| Indicador | Ejecución demostrativa |
| --- | ---: |
| Líneas de prescripción ficticias | **100.000** |
| Líneas marcadas por la regla de demostración | **960** |
| Porcentaje de líneas marcadas | **0,96 %** |
| Semilla del generador | `42` |
| Medicamentos ficticios de la ejecución offline | `100` |

La regla `dosis_mg > 800` se corresponde con valores extremos **inyectados deliberadamente** por el generador. El resultado no constituye una tasa de errores clínicos ni demuestra eficacia predictiva. Se verificó por separado el valor **960/100.000** y el hash de los datos. El archivo [`validation.json`](validation.json) conserva la evidencia.

**Unidad de análisis:** una línea de prescripción; no una persona, receta ni solicitud de reintegro. Un porcentaje segmentado siempre se calcula usando el total de líneas de **ese segmento**, nunca solamente las líneas marcadas.

## Arquitectura

```mermaid
flowchart LR
  A["Catálogo público<br/>openFDA NDC"] --> B["Snapshot local<br/>SHA-256"]
  B --> C["Ingesta Python<br/>upsert"]
  S["Generador sintético<br/>semilla fija"] --> D[("PostgreSQL<br/>dimensiones + hechos")]
  C --> D
  D --> E["Vistas analíticas SQL<br/>total + segmentos"]
  E --> F["Especificación DAX<br/>Power BI"]
  T["Pruebas + CI"] -. validan .-> D
  T -. validan .-> E
```

## Cómo reproducirlo sin base de datos

Requiere Python 3.12 y pip. No necesita internet, openFDA ni PostgreSQL para esta modalidad.

```powershell
git clone https://github.com/metecondrie/auditoria-prescripciones-farmacia.git
cd auditoria-prescripciones-farmacia
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python py/02_generar_sinteticos.py --offline --seed 42 --rows 100000 --report artifacts/validation.json
```

En Linux, activar con `source .venv/bin/activate`. Los tests de PostgreSQL se omiten explícitamente si `TEST_DATABASE_URL` no está definida. En GitHub Actions se ejecutan con PostgreSQL 16. Compará el JSON generado con [el reporte versionado](validation.json).

## Ejecución con PostgreSQL

Usar **una base nueva y exclusiva para pruebas**, PostgreSQL 16+, cliente `psql` y credenciales propias. El DDL no está diseñado como migración de una base preexistente.

```powershell
psql -h localhost -U USUARIO -d audit_demo -v ON_ERROR_STOP=1 -f sql/01_create_tables.sql
psql -h localhost -U USUARIO -d audit_demo -v ON_ERROR_STOP=1 -f sql/02_analytics.sql
$env:DATABASE_URL="postgresql+psycopg://USUARIO:CLAVE@localhost:5432/audit_demo"
python py/01_ingesta_fda.py --download --snapshot artifacts/ndc.json
python py/02_generar_sinteticos.py --seed 42 --rows 100000 --report artifacts/db-validation.json
```

La plantilla [`.env.example`](../.env.example) no se importa automáticamente. No guardes contraseñas reales en el repositorio. Para repetir el mismo catálogo, reutilizá el snapshot y omití `--download`. El resultado de una ejecución online puede diferir de la referencia offline, porque usa otro conjunto de identificadores de medicamentos.

Consultas de análisis:

```sql
SELECT * FROM vw_resumen_auditoria;
SELECT * FROM vw_resumen_por_medicamento;
SELECT * FROM vw_resumen_por_especialidad;
```

Las tasas segmentadas incluyen las líneas normales y marcadas de cada medicamento/especialidad. Los conteos de cada grupo deben sumar el total global.

## Power BI y verificación

El archivo [`Auditoria.pbix`](../powerBI/Auditoria.pbix) es **histórico**. No se verificaron por completo sus relaciones internas, medidas y datos cacheados. No debe tomarse como evidencia visual de la nueva simulación. Las [medidas DAX](../powerBI/medidas.dax) son una especificación para reconstruir el informe sobre la vista completa, no una exportación certificada del PBIX.

Para un tablero renovado: tarjetas de líneas totales, líneas marcadas y tasa, comparaciones por medicamento y especialidad y una tabla de detalle. En poblaciones vacías, el porcentaje debe mostrarse en blanco, no inventar un 0 %.

## Límites y advertencias

La API openFDA NDC solo aporta metadatos de productos; no contiene historiales de recetas ni umbrales clínicos de dosis. Todos los pacientes y médicos son ficticios; sus identificadores `SYN-*` no son hashes de datos reales. No hay clasificación farmacológica de riesgo, comparación entre instituciones, validación clínica ni cálculo fundamentado de ahorros.

Los scripts actuales leen las credenciales desde variables de entorno, pero un commit anterior contenía una credencial incrustada. Si alguna vez fue válida, corresponde revocarla o rotarla: eliminarla de la versión actual no la borra del historial. El PBIX también requiere una revisión de privacidad antes de cualquier reutilización de sus datos internos.

**Documentación adicional:** [contrato analítico](METRICS.md) · [control de calidad](QUALITY.md) · [auditoría técnica inicial](AUDIT.md).

**Autor:** [Alejo Ongaro](https://github.com/metecondrie) · [LinkedIn](https://www.linkedin.com/in/alejo-ongaro-6763871b3/).
