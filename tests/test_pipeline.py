"""Unit tests and PostgreSQL integration tests for the educational ETL."""
import importlib.util
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "py"))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = load("gen", "py/02_generar_sinteticos.py")
fda = load("fda", "py/01_ingesta_fda.py")


class PipelineTests(unittest.TestCase):
    def test_determinism_and_order(self):
        a = gen.generate([3, 1, 2], 1000, 42)
        self.assertEqual(a, gen.generate([2, 3, 1], 1000, 42))
        self.assertNotEqual(a, gen.generate([1, 2, 3], 1000, 43))

    def test_integrity_and_injected_doses(self):
        tables = gen.generate([1, 2], 10000)
        self.assertEqual(len(tables["dim_calendario"]), 731)
        dates = {r["fecha"] for r in tables["dim_calendario"]}
        allowed_doses = {50, 100, 200, 400, 500, 800,
                         5000, 10000, 20000, 40000, 50000, 80000}
        for row in tables["fact_prescripciones"]:
            self.assertIn(row["fecha_prescripcion"], dates)
            self.assertIn(row["id_medicamento"], (1, 2))
            self.assertTrue(1 <= row["id_paciente"] <= 5000)
            self.assertTrue(1 <= row["id_medico"] <= 100)
            self.assertIn(row["dosis_mg"], allowed_doses)
        self.assertGreater(gen.summary(tables, 42)["anomalias_sinteticas"], 0)

    def test_invalid_inputs(self):
        for ids, n in [([], 1), ([1], 0), ([1], -1)]:
            with self.subTest(ids=ids, n=n):
                with self.assertRaises(ValueError):
                    gen.generate(ids, n)

    def test_catalog_cleaning(self):
        rows = fda.normalize({"results": [
            {"product_ndc": " a ", "generic_name": "Compound   A"},
            {"product_ndc": "a", "generic_name": "Compound A"},
            {"generic_name": "missing"},
        ]})
        self.assertEqual(rows, [
            {"codigo_fda": "a", "principio_activo": "Compound A", "nivel_riesgo": None}
        ])
        for payload in (
            {"results": []}, {"results": "not-a-list"}, {},
            {"results": [{"product_ndc": "a", "generic_name": "A"},
                         {"product_ndc": "a", "generic_name": "B"}]},
        ):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    fda.normalize(payload)

    def test_no_default_credentials(self):
        from common import engine_from_env
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                engine_from_env()


@unittest.skipUnless(os.environ.get("TEST_DATABASE_URL"),
                     "PostgreSQL de pruebas no configurado")
class PostgresTests(unittest.TestCase):
    def test_schema_views_and_constraints(self):
        from sqlalchemy import create_engine, text
        from sqlalchemy.exc import IntegrityError
        from common import insert_rows

        engine = create_engine(os.environ["TEST_DATABASE_URL"])
        with engine.connect() as conn:
            transaction = conn.begin()
            try:
                conn.execute(text("CREATE SCHEMA test_auditoria"))
                conn.execute(text("SET LOCAL search_path TO test_auditoria"))
                for name in ["01_create_tables.sql", "02_analytics.sql"]:
                    conn.exec_driver_sql((ROOT / "sql" / name).read_text(encoding="utf-8"))
                conn.execute(text(
                    "INSERT INTO dim_medicamentos(codigo_fda,principio_activo) "
                    "VALUES ('SYN-1','DEMO')"))
                tables = gen.generate([1], 1000)
                for table, rows in tables.items():
                    insert_rows(conn, table, rows)
                total, anomalies, pct = conn.execute(
                    text("SELECT * FROM vw_resumen_auditoria")).one()
                expected = gen.summary(tables, 42)
                self.assertEqual(total, 1000)
                self.assertEqual(anomalies, expected["anomalias_sinteticas"])
                self.assertAlmostEqual(float(pct), expected["porcentaje"])
                with conn.begin_nested() as nested:
                    with self.assertRaises(IntegrityError):
                        conn.execute(text(
                            "INSERT INTO fact_prescripciones("
                            "id_paciente,id_medico,id_medicamento,fecha_prescripcion,"
                            "dosis_mg,cantidad_cajas) VALUES "
                            "(1,1,1,'2024-01-01',-1,1)"))
                    nested.rollback()
            finally:
                transaction.rollback()
        engine.dispose()


if __name__ == "__main__":
    unittest.main()
