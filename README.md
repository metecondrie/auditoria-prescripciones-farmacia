# Pharmacy Prescription Audit

[![CI · Python + PostgreSQL](https://github.com/metecondrie/auditoria-prescripciones-farmacia/actions/workflows/validate.yml/badge.svg)](https://github.com/metecondrie/auditoria-prescripciones-farmacia/actions/workflows/validate.yml)
![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Data](https://img.shields.io/badge/Data-100%25%20synthetic-007f79)

[**Versión en español**](docs/README.es.md) · [Metrics & data contract](docs/METRICS.md) · [Quality & security](docs/QUALITY.md)

![Pharmacy prescription audit — a synthetic data engineering and BI case study](assets/portfolio-cover.svg)

**An end-to-end, reproducible data engineering and business intelligence case study** that turns a public medication product catalogue and synthetic prescription records into a relational model, auditable SQL metrics, and a Power BI reporting specification.

**Important:** This is **not a clinical safety product**. The flagged events, people and prescription lines are simulated. The 800 mg boundary is a generator-specific demonstration rule, not a medically valid maximum dose.

## Project at a glance

| What the project demonstrates | Implementation |
| --- | --- |
| **Data ingestion** | openFDA NDC product metadata, snapshot integrity via SHA-256, idempotent PostgreSQL upsert |
| **Synthetic data engineering** | Deterministic fixed-seed generation, 5,000 fictional patients, 100 fictional physicians, atomic bulk inserts |
| **Relational modeling** | 4 dimensions + a line-level fact table; primary and foreign keys; basic check constraints |
| **Analytics & BI** | SQL detail and aggregate views; global, medication and specialty rates with appropriate denominators |
| **Validation** | Python unit tests, PostgreSQL integration tests, CI workflow, documented reproducibility |
| **Communication** | Explicit metric definitions, limitations, security notes and a traceable reference run |

## Verified demo results


| Synthetic reference run | Result |
| :--- | ---: |
| Prescription lines | **100,000** |
| Lines flagged by the demonstration rule | **960** |
| Flag rate across *all* simulated lines | **0.96%** |
| Random seed | `42` |

These numbers were independently recomputed for the documented offline fixture (100 medication IDs, Python RNG seed 42). They are backed by [`docs/validation.json`](docs/validation.json), its SHA-256 fingerprint, and testable generation code. **They measure the synthetic generator—not real prescription error rates, model accuracy, clinical outcomes or cost reductions.**

For methodology, metric grain and edge cases, see [METRICS.md](docs/METRICS.md).

## Architecture

```mermaid
flowchart LR
    FDA["Public NDC catalogue<br/>openFDA"] --> S["Versionable snapshot<br/>SHA-256"]
    S --> ING["Python ingest<br/>validation + upsert"]
    SYN["Seeded synthetic generator<br/>offline capable"] --> DB[("PostgreSQL<br/>4 dimensions + fact")]
    ING --> DB
    DB --> SQL["Analytical SQL<br/>detail + segment rates"]
    SQL --> BI["Power BI<br/>measure specification"]
    TEST["Unit + database tests<br/>GitHub Actions"] -. verifies .-> SYN
    TEST -. verifies .-> SQL
```

The analysis grain is a **prescription line**, not a unique prescription, claim or patient. Referential integrity is enforced. The medication catalogue does *not* provide dose safety limits.

### Repository map

```text
.
├── assets/
│   └── portfolio-cover.svg           # Project overview graphic
├── py/
│   ├── 01_ingesta_fda.py            # NDC ingestion + reproducible snapshot
│   ├── 02_generar_sinteticos.py     # Deterministic synthetic generator
│   └── common.py                    # Environment-based database configuration
├── sql/
│   ├── 01_create_tables.sql         # Relational schema + constraints
│   └── 02_analytics.sql             # Detail, aggregate & segmented views
├── tests/
│   ├── test_pipeline.py             # Data integrity + PostgreSQL integration
│   └── test_reporting.py            # Fixed-seed and group-rate regression tests
├── powerBI/
│   ├── Auditoria.pbix               # Historical file; not revalidated
│   └── medidas.dax                  # Proposed rebuilding measures
├── docs/
│   ├── METRICS.md                   # Data dictionary and analytical contract
│   ├── QUALITY.md                   # Quality checks and known risks
│   ├── AUDIT.md                     # Original technical audit history
│   └── validation.json             # Reproducible reference-run fingerprint
└── .github/workflows/validate.yml  # Python + PostgreSQL CI
```

## Run in minutes — offline, without PostgreSQL or API access

Requirements: **Python 3.12** and pip. The offline route neither accesses real patient data nor downloads a catalogue.

```bash
git clone https://github.com/metecondrie/auditoria-prescripciones-farmacia.git
cd auditoria-prescripciones-farmacia
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

python -m unittest discover -s tests -v
python py/02_generar_sinteticos.py --offline --seed 42 --rows 100000 --report artifacts/validation.json
```

The command produces a JSON report. Check the flag count, rate, and dataset hash against [the versioned reference](docs/validation.json). Database tests are **skipped** when `TEST_DATABASE_URL` is unset; GitHub Actions runs them with PostgreSQL 16.

## Full PostgreSQL pipeline

Use a **fresh, dedicated demo database**. The schema file is not a migration and should never be applied indiscriminately to an existing database. Requirements: PostgreSQL 16+, the `psql` client, Python 3.12 and an internet connection only for the initial NDC download.

1. Create an empty database of your own, then apply the SQL schema and analytics views:

   ```bash
   psql -h localhost -U YOUR_USER -d audit_demo -v ON_ERROR_STOP=1 -f sql/01_create_tables.sql
   psql -h localhost -U YOUR_USER -d audit_demo -v ON_ERROR_STOP=1 -f sql/02_analytics.sql
   ```

2. Set `DATABASE_URL` in your environment (do **not** commit credentials). A template is available in [`.env.example`](.env.example); it is not automatically loaded.

   ```powershell
   $env:DATABASE_URL="postgresql+psycopg://YOUR_USER:YOUR_PASSWORD@localhost:5432/audit_demo"
   ```

3. Ingest the product catalogue and generate the synthetic fact records:

   ```bash
   python py/01_ingesta_fda.py --download --snapshot artifacts/ndc.json
   python py/02_generar_sinteticos.py --seed 42 --rows 100000 --report artifacts/db-validation.json
   ```

4. Inspect the measures and reconcile the subtotals:

   ```sql
   SELECT * FROM vw_resumen_auditoria;
   SELECT * FROM vw_resumen_por_medicamento;
   SELECT * FROM vw_resumen_por_especialidad;
   ```

To reuse the **same** NDC input, omit `--download` and retain the saved snapshot and reported SHA-256. Data generation intentionally refuses populated fact/dimension destinations, preventing accidental duplicate appends. Since the online NDC catalogue differs from the 100-product offline fixture, its resulting dataset hash need not match the offline reference.

## Power BI dashboard blueprint

![Verified simulated dashboard design preview](assets/dashboard-preview.svg)

This is a **source-backed design preview**, not a screenshot or exported report from the historical `Auditoria.pbix`. The KPI, specialty and monthly values come from [the fixed-seed 100,000-line BI reference](docs/bi_reference.json) and are checked against a fresh generator run in CI.

[Power BI reconstruction guide](powerBI/BUILD_GUIDE.md) · [Importable color theme](powerBI/pharmacy-audit-theme.json) · [DAX measures](powerBI/medidas.dax)

To regenerate the reference without PostgreSQL or Power BI:

```bash
python py/03_export_bi_reference.py --output artifacts/bi_reference.json
```

**Interpretation:** the 24-month variation and specialty differences are random properties of the synthetic generator, not evidence of healthcare trends or differing clinical safety.


## BI: inspectable definitions vs. historical dashboard

The tracked [`powerBI/Auditoria.pbix`](powerBI/Auditoria.pbix) is a **historical artifact**. Its internal model, cached values, visuals and refresh state have **not** been fully verified against the improved SQL schema; do not mistake it for a validated screenshot of the reference run.

For a new dashboard, import `vw_auditoria_prescripciones`, create the measures in [`medidas.dax`](powerBI/medidas.dax), and build a total-lines KPI, a flagged-lines KPI, a flag-rate card, specialty and medication comparisons, and an anomaly drill-through. Keep a single definition of the denominator across filters. A 0-row context should display a blank rate, not an artificial 0%.

## Responsible interpretation & security

- **No real medical claims:** `dosis_mg > 800` is an artificial synthetic rule. No diagnoses, safety thresholds, clinical efficacy or prevention claims.
- **Data provenance:** openFDA NDC is public **product metadata**, not a source of prescriptions or verified maximum doses. The simulated `SYN-*` identifiers are invented, not anonymized real data.
- **Reproducibility:** an earlier, unverified README mentioned 922 flags; the documented fixed-seed run reproduces **960**. See the [technical audit](docs/AUDIT.md).
- **Security:** database credentials are read from environment variables. A prior historical commit contained a credential literal: changing HEAD does **not** erase Git history. Rotate it if it was active. The historical PBIX also requires independent privacy inspection before distribution.
- **Scope:** educational proof of engineering practices, **not** a deployed clinical application or an estimate of monetary savings.

## Author & context

**Alejo Ongaro** — Data Analytics · Python · SQL · Business Intelligence

[GitHub profile](https://github.com/metecondrie) · [LinkedIn](https://www.linkedin.com/in/alejo-ongaro-6763871b3/)

The engineering choices, reproducible calculations and documented limitations are intended to be evaluated directly from the source code and automated tests.
