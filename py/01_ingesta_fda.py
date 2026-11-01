"""Public NDC catalog, not a clinical dose reference."""
import argparse
import hashlib
import json
from pathlib import Path
import requests
from sqlalchemy import text
from common import engine_from_env

URL = "https://api.fda.gov/drug/ndc.json?limit=100"


def normalize(payload):
    rows = {}
    for item in payload["results"]:
        code = item.get("product_ndc")
        name = item.get("generic_name")
        if not code or not name:
            continue
        if len(code) > 100 or len(name) > 255:
            raise ValueError("Catálogo excede las longitudes del esquema")
        rows[code] = {"codigo_fda": code, "principio_activo": name,
                      "nivel_riesgo": None}
    if not rows:
        raise ValueError("Catálogo sin productos válidos")
    return [rows[k] for k in sorted(rows)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()
    if args.download:
        response = requests.get(URL, timeout=(10, 60))
        response.raise_for_status()
        payload = response.json()
        normalize(payload)
        args.snapshot.parent.mkdir(parents=True, exist_ok=True)
        args.snapshot.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    raw = args.snapshot.read_bytes()
    rows = normalize(json.loads(raw))
    engine = engine_from_env()
    with engine.begin() as conn:
        conn.execute(text("""INSERT INTO dim_medicamentos
            (codigo_fda, principio_activo, nivel_riesgo)
            VALUES (:codigo_fda, :principio_activo, :nivel_riesgo)
            ON CONFLICT (codigo_fda) DO UPDATE
            SET principio_activo = EXCLUDED.principio_activo"""), rows)
    print(json.dumps({"productos": len(rows), "snapshot_sha256": hashlib.sha256(raw).hexdigest()}))


if __name__ == "__main__":
    main()
