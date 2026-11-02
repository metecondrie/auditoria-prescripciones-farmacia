# Bitácora — reconstrucción de Power BI (portfolio)

**Proyecto:** Auditoría de prescripciones farmacéuticas (datos 100 % sintéticos).  
**Fecha de inicio de esta bitácora:** 2026-11-02 (Argentina, UTC−03:00).  
**Rama de trabajo:** `improve/portfolio-polish-2026-11-02`.  
**Pull request:** [#2](https://github.com/metecondrie/auditoria-prescripciones-farmacia/pull/2) (borrador, sin fusionar a `main`).

## Convenciones de seguimiento

- **Comprobado:** visible en capturas del usuario o verificado mediante GitHub Actions/código.
- **En curso:** operación iniciada, pero sin verificación final en Power BI Desktop.
- **Pendiente:** no confirmado; nunca dar por completado por inferencia.
- **Límite de acceso:** el PBIX de la computadora lo manipula el usuario. Esta bitácora no implica acceso directo del asistente a la sesión local de Power BI.

## 2026-11-02 — Modernización del repositorio (comprobado)

1. README renovado en inglés y español, portada, caso de estudio para reclutadores, arquitectura y advertencias de simulación.
2. SQL con vistas de agregación por medicamento y especialidad; ingesta Python reforzada; medidas DAX y guía de reconstrucción.
3. Maqueta SVG del dashboard y archivo JSON de referencia, **no** una captura de Power BI ni un PBIX reconstruido.
4. Última ejecución de CI revisada antes de iniciar la reconstrucción local: [12 pruebas aprobadas, PostgreSQL 16 y `pip check`](https://github.com/metecondrie/auditoria-prescripciones-farmacia/actions/runs/41390851869).
5. Indicadores de referencia reproducibles del generador Python: **100.000** líneas sintéticas, **960** marcas demostrativas, **0,96 %**, semilla `42`. Estos números no son tasas de errores clínicos reales.

## 2026-11-02 — Sesión de reconstrucción en Power BI Desktop

### 1. Protección del original — confirmado por el usuario

- Se indicó guardar una copia del informe histórico antes de editarlo.
- El usuario confirmó haber realizado la copia. En las capturas posteriores el archivo aparece como **`Auditoria2`**, con una nueva página de trabajo. **No** afirmar que el asistente guardó o editó directamente ese archivo.
- El panel original contiene 922 marcas y 0,92 % de un conjunto anterior; se conserva como referencia histórica, no como medida equivalente al fixture nuevo.

### 2. Carga de datos sintéticos — confirmado visualmente

- CSV de demostración `Auditoria_Demo_PowerBI.csv` seleccionado desde la interfaz de Power BI.
- La vista previa mostró fechas, IDs, especialidad, medicamento ficticio, dosis, cajas y columna `es_anomalia_demo`.
- Se abrió el Editor de Power Query; los íconos de tipo de columna indicaban fechas, enteros y texto razonablemente compatibles. **No** se ha documentado una auditoría total de nulos/tipos sobre las 100.000 filas desde la interfaz.
- Se renombró la consulta a **`FactPrescripcionesDemo`** y se usó Cerrar y aplicar.
- Confirmación posterior: `FactPrescripcionesDemo` aparece junto a las cinco tablas/consultas antiguas. Todavía **no** se han verificado los KPIs mediante tarjetas.
- Se creó una página nueva llamada **`Dashboard Ejecutivo`**.

### 3. Medidas DAX — estado actual: error por nombre duplicado

En capturas posteriores se observa lo siguiente:

- `Total Prescripciones Demo` está creada bajo `FactPrescripcionesDemo` (ícono de calculadora), pero **falta comprobar el valor en una tarjeta**.
- En el panel hay medidas denominadas `Medida`, `Medida 2` y `Tasa Demo`. El contenido y la validez de las dos primeras aún son **desconocidos**.
- La medida existente `Tasa Demo` muestra un ícono rojo de error.
- En la barra de fórmulas se intentaba crear otra medida con nombre `Tasa Demo` y una referencia a `[Anomalias Demo]`; el cuadro de diálogo de Power BI indicó: **«El nombre 'Tasa Demo' ya se usa en una medida de la tabla 'FactPrescripcionesDemo'. Elija otro nombre»**.
- No se observa en ese panel una medida con nombre `Anomalias Demo`. **No afirmar que esté creada ni que funcione.**

**Corrección indicada al usuario (aún no confirmada):**

1. Cerrar el diálogo de nombre duplicado.
2. Cancelar la nueva definición en edición con la X roja de la barra de fórmulas.
3. Seleccionar la medida **existente** `Tasa Demo` y reemplazarla por:

```dax
Tasa Demo =
DIVIDE(
    SUM('FactPrescripcionesDemo'[es_anomalia_demo]),
    [Total Prescripciones Demo]
)
```

4. Presionar Enter; comprobar que desaparezca el error, y configurar formato **Porcentaje**, dos decimales.
5. Crear o reparar una medida separada `Anomalias Demo = SUM('FactPrescripcionesDemo'[es_anomalia_demo])`; revisar el contenido de `Medida` / `Medida 2` **antes** de borrarlas.

### 4. Pendientes de validación en Power BI

- [ ] Confirmar en captura que `Tasa Demo` ya no contiene error y que no quedan medidas duplicadas/rotas.
- [ ] Confirmar la medida `Anomalias Demo` con ícono de calculadora.
- [ ] Insertar las tres tarjetas (total, marcas, tasa); comprobar **100.000**, **960**, **0,96 %**, respectivamente, sin filtros.
- [ ] Validar el modelo y las interacciones al filtrar por especialidad/medicamento/fecha, sin sumar porcentajes de grupos.
- [ ] Aplicar fondo, retícula, tema y jerarquía visual definidos en [BUILD_GUIDE.md](../powerBI/BUILD_GUIDE.md).
- [ ] Crear gráficos de especialidad, evolución mensual y tabla de exploración, utilizando exclusivamente `FactPrescripcionesDemo` para la nueva página.
- [ ] Validar medidas, unidades, tooltips, distribución, contraste y legibilidad a distintas escalas.
- [ ] Guardar la **copia nueva** del PBIX, reabrir y verificar; evaluar su incorporación al repositorio únicamente después de revisarlo.
- [ ] Revisar el histórico `powerBI/Auditoria.pbix` y credenciales antiguas antes de considerar distribución pública segura.
- [ ] No fusionar PR #2 ni reemplazar el PBIX histórico sin comprobaciones y autorización del usuario.

## Principio de interpretación

Todas las marcas del proyecto nuevo proceden de una **simulación reproducible**. La regla `dosis_mg > 800` **no** es un umbral farmacológico ni define seguridad clínica. El objetivo es demostrar ingeniería de datos, modelado, trazabilidad y visualización auditable, no diagnosticar pacientes ni estimar ahorros reales.

---
**Próxima actualización:** después de recibir una captura con la medida `Tasa Demo` corregida; agregar una nueva entrada con fecha, observación verificable y paso siguiente.
