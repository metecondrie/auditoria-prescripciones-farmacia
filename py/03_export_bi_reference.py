"""Export deterministic BI reference aggregates from the original generator.

No live NDC catalogue, credentials, database or patient records are required.
This is demonstration data, not an estimate of clinical outcomes.
"""
import argparse
from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "py"))
SPEC = importlib.util.spec_from_file_location(
    "pharmacy_sim", ROOT / "py" / "02_generar_sinteticos.py"
)
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)

EXPECTED_HASH = "fca80e529a3bc5ac765f5642f10e79c3bfcc169d625705dc7c17257d2c500247"


def build_reference():
    tables = GENERATOR.generate(range(1, 101), n=100000, seed=42)
    digest = hashlib.sha256(
        json.dumps(tables, default=str, sort_keys=True).encode()
    ).hexdigest()
    if digest != EXPECTED_HASH:
        raise ValueError("Fixture hash changed; review the methodology before updating reference metrics")

    specialties = {item["id_medico"]: item["especialidad"] for item in tables["dim_medicos"]}
    by_specialty = defaultdict(lambda: [0, 0])
    by_month = defaultdict(lambda: [0, 0])
    for item in tables["fact_prescripciones"]:
        flag = int(item["dosis_mg"] > 800)
        month = item["fecha_prescripcion"].strftime("%Y-%m")
        for group in (by_specialty[specialties[item["id_medico"]]], by_month[month]):
            group[0] += 1
            group[1] += flag

    def rows(aggregates, label_key):
        return [
            {label_key: key, "total_lines": values[0],
             "flagged_lines": values[1],
             "flagged_rate_pct": round(100 * values[1] / values[0], 4)}
            for key, values in sorted(aggregates.items())
        ]

    total = len(tables["fact_prescripciones"])
    flags = sum(value[1] for value in by_specialty.values())
    report = {
        "dataset_sha256": digest,
        "seed": 42,
        "total_lines": total,
        "flagged_lines": flags,
        "flagged_rate_pct": round(100 * flags / total, 4),
        "by_specialty": rows(by_specialty, "specialty"),
        "by_month": rows(by_month, "month"),
    }
    for segment in (report["by_specialty"], report["by_month"]):
        assert sum(item["total_lines"] for item in segment) == total
        assert sum(item["flagged_lines"] for item in segment) == flags
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "bi_reference.json")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(build_reference(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Exported reference: {args.output}")


if __name__ == "__main__":
    main()
