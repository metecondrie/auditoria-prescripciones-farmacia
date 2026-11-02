# Case study — Pharmacy Prescription Audit

**Portfolio project · Python / PostgreSQL / SQL analytics / Power BI specification**

[Back to the project](../README.md) · [Spanish overview](README.es.md) · [Data contract](METRICS.md) · [Dashboard preview](../assets/dashboard-preview.svg)

## The problem being demonstrated

A reporting system is only as trustworthy as its **source provenance, analysis grain, metric definitions and reproducibility**. This project asks an educational question: *Can a pharmacy-themed analytical pipeline be reconstructed from source, with every published demo metric independently checkable?*

This is a **synthetic engineering exercise**, not a study of a pharmacy, insurer or hospital. There were no real prescriptions, no institution-specific business requirements and no measured savings.

## Engineering approach

1. **Extract:** read a small public openFDA NDC product catalogue snapshot. Validate its structure and NDC identifiers, reject conflicting duplicates, preserve the raw snapshot and SHA-256, and make ingestion idempotent through database upserts. The catalogue contains **product information**, not safe-dose limits.
2. **Generate:** create 5,000 fictional patient identities, 100 fictional physicians, date dimensions and 100,000 line-level facts using Python's seedable RNG. Inject a roughly 1% share of artificial outliers by multiplying some selected dose values by 100.
3. **Model:** load a PostgreSQL star-like schema with four dimensions, a line-level fact table, explicit keys, mandatory relationships and numeric integrity constraints. Reject nonempty target tables for fact generation and perform inserts inside one transaction.
4. **Analyze:** expose full-grain detail, flagged-line detail, overall totals, medication-specific rates and specialty-specific rates through SQL views.
5. **Verify:** assert deterministic output and SHA-256; reconcile the flagged predicate against row-level records; test SQL vs Python aggregates, empty-population behavior, reference integrity and absence of joined-row multiplication.
6. **Communicate:** provide clear definitions, a documented DAX rebuild specification, a Power BI visual theme and a dashboard **design preview** generated from reproducible synthetic aggregates.

## Results and exact interpretation

| Reference run | Verified output |
| --- | ---: |
| Seed | 42 |
| Offline medication IDs | 100 |
| Prescription lines | **100,000** |
| Flagged synthetic lines | **960** |
| Flagged share | **0.96%** |

**The 960 records were artificially constructed to exceed the rule `dosis_mg > 800`.** Thus the count demonstrates the generator and the SQL definition, not a model that detects actual unsafe prescribing. It would be inappropriate to claim classifier accuracy, prevention, reduced harm or institutional performance.

The reference dataset's SHA-256 is `fca80e529a3bc5ac765f5642f10e79c3bfcc169d625705dc7c17257d2c500247`. [The exported BI reference](bi_reference.json) contains month and specialty aggregates with both numerators and denominators; the generator recomputes them in CI.

## Five technical decisions worth reviewing

| Decision | Why it matters | Tradeoff |
| --- | --- | --- |
| Deterministic RNG + hash | Regression tests detect changes in fixture generation or ordering | The fixture is not representative of real prescribing |
| Full-line denominators | Avoids meaningless 100% rates when only flagged lines are queried | The semantics must be preserved through BI filters |
| Database constraints + atomic load | Prevents inconsistent rows and silent duplicate appends | Requires a dedicated fresh database for each run |
| Snapshot and NDC upsert | Provides provenance and repeatable ingestion | The NDC endpoint sample does not represent every drug |
| Clear boundary between SQL and legacy PBIX | Avoids claiming unverified visuals are supported by current metrics | Rebuilding and validating a true PBIX requires Power BI Desktop |

## How a reviewer can evaluate the work

On Python 3.12:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python py/02_generar_sinteticos.py --offline --seed 42 --rows 100000 --report artifacts/validation.json
python py/03_export_bi_reference.py --output artifacts/bi_reference.json
```

Compare both reports with [validation.json](validation.json) and [bi_reference.json](bi_reference.json). Integration tests require `TEST_DATABASE_URL`; GitHub Actions provisions PostgreSQL 16.

For the visual design, review the [dashboard preview](../assets/dashboard-preview.svg) and [Power BI build guide](../powerBI/BUILD_GUIDE.md). **The preview is not a validated PBIX export.**

## What production readiness would require

With legitimately authorized real data and expert supervision, a future system would need a formal data contract, stronger quality monitoring, drug identifier normalization, clinical ontology, patient-specific medication context, access controls, privacy review, migration and backfill strategy, orchestrated ETL, performance tests, traceable source snapshots, and review/validation by qualified clinical professionals.

None of those activities can be inferred from this portfolio demonstration. Similarly, the historical `Auditoria.pbix` binary is retained for provenance but its compressed model has **not** been audited completely.

---

**Portfolio takeaway:** a small, transparent analytics system is more credible when a reader can reproduce its numbers, inspect its assumptions and identify exactly where its claims stop.
