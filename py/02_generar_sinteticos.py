"""Deterministic educational fixtures. No real patient identities."""
import argparse
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
import random
from sqlalchemy import text
from common import engine_from_env, insert_rows


def generate(medication_ids, n=100000, seed=42):
    ids = sorted(set(medication_ids))
    if not ids or n < 1:
        raise ValueError("Se requieren medicamentos y n positivo")
    rng = random.Random(seed)
    start = date(2024, 1, 1)
    dates = [start + timedelta(days=i) for i in range(731)]
    calendar = [{"fecha": d, "anio": d.year, "mes": d.month,
                 "dia_semana": d.weekday(), "es_feriado": None} for d in dates]
    patients = [{"id_paciente": i, "hash_identidad": f"SYN-P-{seed}-{i}",
                 "fecha_nacimiento": date(1950, 1, 1) + timedelta(days=rng.randrange(20000)),
                 "genero": rng.choice(["M", "F", "X", None])} for i in range(1, 5001)]
    specialties = ["Psiquiatría", "Traumatología", "Clínica Médica", "Neurología", "Oncología"]
    doctors = [{"id_medico": i, "matricula_hash": f"SYN-M-{seed}-{i}",
                "especialidad": rng.choice(specialties), "valido_desde": start,
                "valido_hasta": None, "es_actual": True} for i in range(1, 101)]
    facts = []
    for _ in range(n):
        dose = rng.choice([50, 100, 200, 400, 500, 800])
        if rng.random() < 0.01:
            dose *= 100
        facts.append({"id_paciente": rng.randrange(1, 5001), "id_medico": rng.randrange(1, 101),
                      "id_medicamento": rng.choice(ids), "fecha_prescripcion": rng.choice(dates),
                      "dosis_mg": dose, "cantidad_cajas": rng.randrange(1, 6)})
    return {"dim_calendario": calendar, "dim_pacientes": patients,
            "dim_medicos": doctors, "fact_prescripciones": facts}


def summary(tables, seed):
    facts = tables["fact_prescripciones"]
    anomalies = sum(r["dosis_mg"] > 800 for r in facts)
    digest = hashlib.sha256(json.dumps(tables, default=str, sort_keys=True).encode()).hexdigest()
    return {"seed": seed, "total": len(facts), "anomalias_sinteticas": anomalies,
            "porcentaje": 100 * anomalies / len(facts), "dataset_sha256": digest,
            "regla_demo": "dosis_mg > 800; no es un umbral clínico"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=100000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--offline", action="store_true", help="Validación sin base ni red")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.offline:
        tables = generate(range(1, 101), args.rows, args.seed)
    else:
        engine = engine_from_env()
        with engine.begin() as conn:
            # Serialize generation and reject populated targets; no partial append.
            conn.execute(text("LOCK TABLE dim_medicamentos, dim_calendario, dim_pacientes, dim_medicos, fact_prescripciones IN EXCLUSIVE MODE"))
            for table in ["dim_calendario", "dim_pacientes", "dim_medicos", "fact_prescripciones"]:
                if conn.execute(text(f"SELECT EXISTS (SELECT 1 FROM {table})")).scalar():
                    raise ValueError("Destino no vacío: usá una base de demostración nueva")
            ids = list(conn.execute(text("SELECT id_medicamento FROM dim_medicamentos ORDER BY id_medicamento")).scalars())
            tables = generate(ids, args.rows, args.seed)
            for table, rows in tables.items():
                insert_rows(conn, table, rows)
    report = json.dumps(summary(tables, args.seed), indent=2, ensure_ascii=False)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report + "\n", encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
