# Auditoría de prescripciones farmacéuticas

**Caso de portfolio · Ingeniería de datos y BI · Datos sintéticos**

Pipeline educativo para explorar anomalías de dosificación simuladas con Python,
PostgreSQL y Power BI. Demuestra ingesta, modelo dimensional, controles de calidad,
vistas analíticas y validaciones reproducibles. No es un sistema clínico ni opera en tiempo real.

## Evidencia reproducible

La ejecución offline con Python 3.12, semilla 42, 100 medicamentos ficticios y
100.000 líneas genera **960 anomalías sintéticas (0,96%)**. El resultado describe
el generador; no mide errores de una institución, precisión clínica ni impacto económico.
[Reporte y hash](docs/validation.json) · [Auditoría técnica](docs/AUDIT.md)

## Arquitectura

```mermaid
flowchart LR
    A[Catálogo público openFDA NDC] --> B[Snapshot local y hash]
    B --> C[Ingesta con upsert]
    S[Generador sintético con semilla] --> D[PostgreSQL: 4 dimensiones y hechos]
    C --> D
    D --> E[Vistas SQL: detalle, anomalías y resumen]
    E --> F[Power BI: reconstrucción documentada]
```

El grano es una línea de prescripción. Las dimensiones son paciente ficticio,
médico ficticio, medicamento y fecha. El catálogo NDC no aporta dosis máximas
ni una clasificación clínica de riesgo. `nivel_riesgo` queda sin asignar.

## Reproducción sin red ni base

```powershell
python -m venv .venv
.venv/Scripts/Activate.ps1
pip install -r requirements.txt
python -m unittest discover -s tests -v
python py/02_generar_sinteticos.py --offline --seed 42 --rows 100000 --report artifacts/validation.json
```

Sin `TEST_DATABASE_URL` se omite explícitamente la prueba de integración.
En Linux, activar con `source .venv/bin/activate`.

## Pipeline PostgreSQL (base nueva de demostración)

Requiere PostgreSQL 16 o posterior, Python 3.12 y cliente psql. No ejecutar el DDL
sobre una base con datos existentes: esta versión no incluye una migración.
Configurar credenciales propias mediante variables de entorno; `.env.example`
es una plantilla y no se carga automáticamente.

```powershell
$env:DATABASE_URL='postgresql+psycopg://USER:PASSWORD@localhost:5432/auditoria_farmaco'
psql -h localhost -U USER -d auditoria_farmaco -v ON_ERROR_STOP=1 -f sql/01_create_tables.sql
psql -h localhost -U USER -d auditoria_farmaco -v ON_ERROR_STOP=1 -f sql/02_analytics.sql
python py/01_ingesta_fda.py --download --snapshot artifacts/ndc.json
python py/02_generar_sinteticos.py --seed 42 --rows 100000 --report artifacts/db-validation.json
```

Para repetir la ingesta con el mismo catálogo, omitir `--download`: el snapshot
y su SHA-256 identifican la fuente. La selección de medicamentos del endpoint
puede variar con el tiempo. La generación rechaza destinos poblados y usa una
transacción para impedir cargas parciales. Usar otra base nueva para repetirla.
La ingesta de catálogo es idempotente por `codigo_fda`.

```powershell
$env:TEST_DATABASE_URL=$env:DATABASE_URL
python -m unittest discover -s tests -v
```

La integración usa un esquema de prueba en una transacción que se revierte.
[Workflow CI](.github/workflows/validate.yml) ejecuta la prueba con PostgreSQL 16.

## Metodología y límites

- Regla demostrativa: `dosis_mg > 800`. Separa dosis base (50–800) de valores
  multiplicados por 100 por el generador; no evalúa toxicidad ni dosis seguras.
- Probabilidad de inyección: 1%; el porcentaje observado no tiene que ser 1% exacto.
- Denominador: todas las líneas en el contexto de filtro. No contar solo la vista
  de anomalías para calcular el porcentaje.
- El umbral de visualización de 1% es ilustrativo. No está validado clínicamente.
- Identidades `SYN-*` y fechas son ficticias, no hashes de pacientes reales.
  No hay una evaluación de anonimización de datos reales.
- No se simulan feriados oficiales (`NULL`), ni historial SCD2 de médicos:
  cada médico tiene una sola versión vigente.
- No se demuestra despliegue, prevención de eventos, ahorro, sensibilidad o especificidad.

## Power BI

Se conserva `powerBI/Auditoria.pbix` como artefacto histórico, sin modificarlo.
La inspección del contenedor encontró una página con cuatro visuales y referencias
al esquema `analytics` y `raw` que no existían en el SQL original. No se ejecutó
Power BI Desktop ni se refrescó el modelo binario: los números del PBIX no son
la evidencia de la nueva simulación.

Para reconstruir: importar `vw_auditoria_prescripciones`, usar
[medidas.dax](powerBI/medidas.dax), formatear la razón como porcentaje y agregar
segmentador por especialidad, tarjeta de anomalías y barras por principio activo.
Una suma por medicamento mide volumen; para tasa, dividir por las líneas de ese
medicamento. El archivo DAX es una especificación para reconstrucción, no una
exportación validada del modelo histórico.

## Seguridad y fuentes

Se retiró una credencial incrustada de los scripts actuales. Sigue presente en
el historial previo: cambiarla si continúa vigente. No se reescribió historial.
No publicar el PBIX como fuente anonimizada: su DataModel comprimido no se auditó
por completo. No cargar datos de personas reales para esta demostración.

Fuente de catálogo: [openFDA NDC](https://open.fda.gov/apis/drug/ndc/).
El README original reportaba 922 anomalías sin snapshot ni semilla verificables;
se conserva ese antecedente en la auditoría, sin presentarlo como resultado reproducido.
