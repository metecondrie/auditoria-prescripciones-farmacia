# Auditoría de Prescripciones Farmacéuticas 

**Objetivo:** Monitorear el índice de riesgo en la emisión de recetas médicas para detectar posibles dosis letales y errores administrativos en tiempo real.

##  Tecnologías Utilizadas
* **PostgreSQL:** Almacenamiento, limpieza de datos (SQL) y creación de vistas analíticas.
* **Power BI:** Modelado de datos (Esquema en Estrella) y visualización de KPIs.
* **DAX:** Creación de medidas dinámicas de riesgo.

##  Arquitectura del Proyecto
1. **Extracción y Transformación (ETL):** Conexión a PostgreSQL. Limpieza y extracción de vistas usando Power Query.
2. **Modelado Relacional:** Implementación de un modelo de datos conectando la tabla de hechos (recetas) con sus dimensiones (medicamentos, médicos).
3. **Métricas Clave:** Cálculo de un *Índice de Riesgo* dinámico estableciendo un umbral de tolerancia del 1.00%.

##  Insights del Dashboard
* Se procesaron 100.000 recetas, detectando un volumen de **922 anomalías** (0.92% de riesgo operativo).
* Mediante un análisis Top 10 (Treemap), se identificaron los fármacos que concentran la mayor tasa de error, habilitando una intervención directa por especialidad médica.
