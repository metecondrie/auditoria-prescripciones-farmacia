# Revisión técnica — 2026-11-01

Base revisada: `96ae405`. Se leyeron todos los archivos de código y SQL del
repositorio, README y estructura del SVG; se inspeccionaron entradas ZIP,
metadatos y configuración de visuales del PBIX. No había pruebas, dependencias
fijadas, vistas analíticas SQL ni instrucciones completas de reproducción.

| Hallazgo original | Mejora / evidencia |
|---|---|
| Credenciales incrustadas en ambos scripts | DATABASE_URL, sin conexión al importar; .gitignore |
| Aleatoriedad y fechas relativas no controladas | RNG local, semilla, fechas fijas, hash de dataset |
| Reejecución parcial por múltiples append | Transacción única y rechazo de tablas pobladas |
| Catálogo duplicado en reingestas | Clave única, upsert y snapshot con hash |
| Riesgo clínico asignado al azar | NULL; se documenta ausencia de referencia clínica |
| Feriados aleatorios y SCD2 solo declarado | Feriados desconocidos, SCD2 no implementado explícito |
| Sin vistas en el repositorio | Tres vistas con denominador completo y división segura |
| Sin control de dosis/cajas ni FK obligatorias | CHECK y NOT NULL; prueba PostgreSQL |
| 922 anomalías no reproducibles | Nueva ejecución independiente: 960/100000, 0,96% |
| PBIX usa analytics/raw no presentes en DDL | Preservado como histórico; especificación DAX separada |

## Verificación local

Python 3.12, PostgreSQL 18 en clúster temporal aislado; 6 pruebas aprobadas,
ninguna omitida. Integración: creación del esquema y vistas, carga sintética de
1000 líneas, comparación de agregados SQL con Python y rechazo de entrada inválida.
Ejecución offline de 100000 líneas: ver `validation.json` (semilla y hash).
Además se ejecutó el CLI completo con 100000 filas en PostgreSQL: SQL devolvió
100000 / 960 / 0,96%; el hash coincidió con la ejecución offline. Una segunda
carga fue rechazada y conservó exactamente 100000 filas.
CI propuesto en PostgreSQL 16; su estado debe consultarse en GitHub, no se infiere
del resultado local.

## Límites de cobertura

El DataModel del PBIX es binario comprimido: no se verificaron fórmulas DAX,
Power Query, relaciones internas, cachés ni cada valor almacenado. El layout
muestra gauge, slicer, cardVisual y treemap; no demuestra resultados ni actualización.
El SVG original es un diagrama dimensional; se conserva. No hay datos tabulares
versionados fuera del PBIX. No se afirmó ausencia de información sensible en ese
modelo; no se reutilizó su imagen ni sus números como evidencia nueva.

No se usa una base real ni se borran datos existentes. El DDL cambió para bases
nuevas; requiere migración revisada antes de aplicarlo a una instalación existente.
No se validó eficacia clínica, desempeño de producción, actualización en tiempo
real, ni impacto en instituciones. Las 922 anomalías del README anterior quedan
como antecedente no reproducido. La nueva cifra mide outliers inyectados.
