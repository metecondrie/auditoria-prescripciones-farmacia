"""Independent regression checks for reported portfolio metrics.

The fixed-seed fixture is a *software* regression, never clinical validation.
Database tests run only when TEST_DATABASE_URL is configured.
"""
from collections import Counter
import importlib.util
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "py"))
spec = importlib.util.spec_from_file_location("generator_reporting", ROOT / "py" / "02_generar_sinteticos.py")
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


class OfflineReportingTests(unittest.TestCase):
    def test_fixed_seed_reference_and_denominator(self):
        tables = generator.generate(range(1, 101), n=1000, seed=42)
        report = generator.summary(tables, seed=42)
        # Independent expected values captured from the original reference run.
        self.assertEqual(report["total"], 1000)
        self.assertEqual(report["anomalias_sinteticas"], 14)
        self.assertEqual(report["porcentaje"], 1.4)
        self.assertEqual(
            report["dataset_sha256"],
            "e13b9c8e4a4158a072d7e8d214c4c3d763832829f2a08f116b6da29da23d545b",
        )
        # Verify the predicate independently of the report implementation.
        self.assertEqual(sum(item["dosis_mg"] > 800 for item in tables["fact_prescripciones"]), 14)

    def test_all_prescriptions_belong_to_exactly_one_specialty(self):
        tables = generator.generate([3, 1, 2], n=1200, seed=7)
        specialties = {doctor["id_medico"]: doctor["especialidad"] for doctor in tables["dim_medicos"]}
        by_specialty = Counter(specialties[p["id_medico"]] for p in tables["fact_prescripciones"])
        self.assertEqual(sum(by_specialty.values()), 1200)
        self.assertEqual(len(tables["fact_prescripciones"]), 1200)


@unittest.skipUnless(os.getenv("TEST_DATABASE_URL"), "TEST_DATABASE_URL is not configured")
class ReportingIntegrationTests(unittest.TestCase):
    def test_empty_and_segmented_sql_aggregates(self):
        from sqlalchemy import create_engine, text
        from common import insert_rows

        engine = create_engine(os.environ["TEST_DATABASE_URL"])
        with engine.connect() as conn:
            transaction = conn.begin()
            try:
                # Isolated transaction: never modifies application schemas.
                conn.execute(text("CREATE SCHEMA test_auditoria_reporting"))
                conn.execute(text("SET LOCAL search_path TO test_auditoria_reporting"))
                for sql_file in ("01_create_tables.sql", "02_analytics.sql"):
                    conn.exec_driver_sql((ROOT / "sql" / sql_file).read_text(encoding="utf-8"))

                empty = conn.execute(text("SELECT * FROM vw_resumen_auditoria")).one()
                self.assertEqual(tuple(empty), (0, 0, None))
                self.assertEqual(conn.execute(text("SELECT COUNT(*) FROM vw_resumen_por_medicamento")).scalar(), 0)

                conn.execute(text("""INSERT INTO dim_medicamentos
                    (codigo_fda, principio_activo) VALUES
                    ('SYN-A', 'Compound A'), ('SYN-B', 'Compound B')"""))
                tables = generator.generate([1, 2], n=1500, seed=42)
                for name, rows in tables.items():
                    insert_rows(conn, name, rows)

                totals = conn.execute(text("SELECT * FROM vw_resumen_auditoria")).one()
                self.assertEqual(totals.total_prescripciones, 1500)
                expected_anomalies = sum(p["dosis_mg"] > 800 for p in tables["fact_prescripciones"])
                self.assertEqual(totals.anomalias, expected_anomalies)
                self.assertAlmostEqual(float(totals.porcentaje_anomalias), 100 * expected_anomalies / 1500)

                med_rows = conn.execute(text(
                    "SELECT id_medicamento, total_prescripciones, anomalias, porcentaje_anomalias "
                    "FROM vw_resumen_por_medicamento"
                )).mappings().all()
                expected_med = Counter(p["id_medicamento"] for p in tables["fact_prescripciones"])
                self.assertEqual({r["id_medicamento"]: r["total_prescripciones"] for r in med_rows}, dict(expected_med))
                self.assertEqual(sum(r["anomalias"] for r in med_rows), expected_anomalies)
                for r in med_rows:
                    self.assertAlmostEqual(
                        float(r["porcentaje_anomalias"]),
                        100 * r["anomalias"] / r["total_prescripciones"],
                    )

                specialty_by_doctor = {
                    d["id_medico"]: d["especialidad"] for d in tables["dim_medicos"]
                }
                expected_specialties = Counter(
                    specialty_by_doctor[p["id_medico"]] for p in tables["fact_prescripciones"]
                )
                sql_specialties = conn.execute(text(
                    "SELECT especialidad, total_prescripciones, anomalias "
                    "FROM vw_resumen_por_especialidad"
                )).mappings().all()
                self.assertEqual(
                    {r["especialidad"]: r["total_prescripciones"] for r in sql_specialties},
                    dict(expected_specialties),
                )
                self.assertEqual(sum(r["anomalias"] for r in sql_specialties), expected_anomalies)

                # Check grain preservation after dimensional joins.
                self.assertEqual(
                    conn.execute(text("SELECT COUNT(*) FROM vw_auditoria_prescripciones")).scalar(), 1500
                )
                self.assertEqual(
                    conn.execute(text("SELECT COUNT(*) FROM vw_auditoria_anomalias")).scalar(),
                    expected_anomalies,
                )
            finally:
                transaction.rollback()
        engine.dispose()


if __name__ == "__main__":
    unittest.main()
