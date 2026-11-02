# Quality gates and evidence

## Automated checks

| Control | Code and evidence |
| --- | --- |
| Deterministic generator and 1,000-line reference fingerprint | `tests/test_pipeline.py`, `tests/test_reporting.py` |
| Enforced keys, mandatory foreign keys and positive dose/boxes | `sql/01_create_tables.sql` and integration test |
| Single-transaction synthetic load; nonempty target rejected | `py/02_generar_sinteticos.py` |
| Catalogue deduplication and idempotent upsert | `py/01_ingesta_fda.py` |
| Credentials read from environment, not hardcoded at runtime | `py/common.py` |
| Correct group-specific denominators and joined grain | `sql/02_analytics.sql`, `tests/test_reporting.py` |
| Empty input produces NULL/BLANK rate rather than 0% | SQL integration test and `powerBI/medidas.dax` |
| Python 3.12 + PostgreSQL 16 continuous integration | `.github/workflows/validate.yml` |

Without `TEST_DATABASE_URL`, integration tests are intentionally **skipped**; a successful offline-only run does not certify PostgreSQL behavior. Verify the status of the actual proposed branch on the GitHub Actions page.

## Known security risks

1. **Git history:** a prior commit contained a credential literal. HEAD was cleaned, but history is not rewritten. Revoke or rotate it if it was real and active.
2. **Historical PBIX:** the compressed DataModel has not been comprehensively audited. Do not claim the binary is privacy-safe or reuse its cached values as current evidence.
3. **Secrets and fixtures:** never commit live credentials, patient information, unreviewed NDC snapshots or private CSV extracts. The synthetic identifiers are invented and not hashes of real people.
4. **External catalogue:** openFDA may change. Keep and identify a local snapshot and its checksum for any comparative run.

## Release checklist

1. Verify CI is green **including PostgreSQL integration tests** for this branch.
2. Generate the 100,000-line offline reference; compare total, flags, rate and SHA-256 with `docs/validation.json`.
3. Query both group views and reconcile their numerator/denominator sums against the global totals.
4. Review GitHub-rendered README text, banner and relative links.
5. If publishing a new Power BI screenshot, refresh the actual PBIX, inspect its data model and reconcile every shown value; otherwise leave the historical file clearly labeled.
6. Double-check there are no credentials, real-world identities or clinical-safety claims.

## Limitations

The rule is intentionally artificial; real dose ranges, frequency, route, drug interactions and patient characteristics are absent. The NDC endpoint represents only a limited catalogue slice, not exhaustive coverage. Physician history is not modeled as SCD2, and the retained Power BI binary is unverified. CI is evidence of specific checks, not a claim of production readiness.
