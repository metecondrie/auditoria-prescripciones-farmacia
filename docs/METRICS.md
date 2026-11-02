# Metrics, lineage and analytical contract

> **Scope:** a reproducible synthetic-data demonstration of an ETL + SQL + BI workflow. It does not use patient records or implement clinical risk assessment.

## Data model and grain

| Table or view | Grain | Definition |
| --- | --- | --- |
| `dim_pacientes` | One fictitious person | `id_paciente`; `hash_identidad` is an invented SYN label, not a cryptographic patient hash. |
| `dim_medicos` | One fictitious physician | `id_medico`; no Type 2 history is implemented. |
| `dim_medicamentos` | One NDC product | `id_medicamento`; `codigo_fda` has a unique constraint. |
| `dim_calendario` | One date | 2024-01-01 through 2025-12-31 (731 days). Holiday labels are unknown. |
| `fact_prescripciones` | One prescription **line** | `id_prescripcion_linea`; one line is not necessarily one claim/patient. |
| `vw_auditoria_prescripciones` | One line | Joined detail and simulated flag. |
| `vw_auditoria_anomalias` | One flagged line | Drill-through only: not an eligible denominator. |
| `vw_resumen_auditoria` | One total | Count, number flagged, rate. Empty result uses NULL for rate. |
| `vw_resumen_por_medicamento` | One medication with lines | Medication-specific counts and rate. |
| `vw_resumen_por_especialidad` | One specialty with lines | Specialty-specific counts and rate. |

The generator produces 5,000 fictitious patients and 100 fictitious physicians. The 100 demonstration medication IDs are used in the **offline** reference; the online NDC response may yield a different number of usable products.

## Metric definitions

Let N be the total count of lines in the selected context, and A the number whose `dosis_mg > 800`.

- **Total lines:** N = COUNT(*).
- **Demo flags:** A = sum of the Boolean predicate (`dosis_mg > 800`).
- **Demo rate:** 100 × A / N percent; undefined, represented as SQL NULL, if N = 0.
- **Medication/specialty rates:** calculate each group's own total and flagged count before dividing.

The generator chooses base doses from {50, 100, 200, 400, 500, 800}, multiplying approximately 1% by 100. All injected outliers then exceed the rule boundary **by design**. This is not a clinically validated classifier, and claiming perfect model precision or sensitivity from it would be circular.

A real dose assessment would require dose units, route, frequency, drug strength, clinical context and patient-specific variables, none of which are represented in this simulation.

## Reproducible reference run

| Parameter | Value |
| --- | --- |
| Python | 3.12 in CI |
| Random seed | 42 |
| Offline medication IDs | 1 through 100 |
| Lines | **100,000** |
| Demo flags | **960** |
| Demo rate | **0.96%** |
| Date range | 2024-01-01 to 2025-12-31 |
| SHA-256 of serialized synthetic tables | `fca80e529a3bc5ac765f5642f10e79c3bfcc169d625705dc7c17257d2c500247` |

Evidence: [validation.json](validation.json), the deterministic Python generator, and the regression tests. SHA-256 covers JSON serialization of all generated tables with sorted keys and date serialization; it is not a hash of a medical dataset.

To recreate:

```bash
python py/02_generar_sinteticos.py --offline --seed 42 --rows 100000 --report artifacts/validation.json
python -m unittest discover -s tests -v
```

The original README quoted **922** flags without a verifiable source/snapshot/seed. It is preserved as an unverified historical figure in [AUDIT.md](AUDIT.md), **not** as a reproduced metric. The nominal injection probability of 1% does not imply exactly 1% on every run.

## Group reconciliation

```sql
SELECT * FROM vw_resumen_auditoria;
SELECT * FROM vw_resumen_por_medicamento;
SELECT * FROM vw_resumen_por_especialidad;
```

For a fully loaded, unfiltered model, summing each medication group's **counts** and **flag counts** separately must reproduce the total measures. The same holds across specialties. Never sum percentages, take a simple mean of group rates, or divide the flagged-detail view by itself.

**Empty populations:** SQL's global percentage is NULL and the proposed DAX measure is BLANK(), rather than falsely displaying 0%.

**BI caveat:** the tracked PBIX is historical; its internal DAX model and cached figures have not been comprehensively verified against these views.

## Interpretation boundaries

- openFDA NDC is a **public product catalogue**, not a dose safety reference or source of prescriptions.
- These figures describe a random generator, not an institution's error rate, treatment safety or savings.
- Random specialty/medication differences are not estimates of real-world comparative risk.
- Neither the 1% synthetic injection probability nor the 800 mg demo rule is a clinical threshold.
- No real patient identifiers were read, hashed or anonymized. All `SYN-*` labels are fictional.
