"""Reproducible ingestion of public NDC *product* metadata, not clinical doses."""
import argparse
import hashlib
import json
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from sqlalchemy import text
from common import engine_from_env

URL = "https://api.fda.gov/drug/ndc.json?limit=100"


def normalize(payload):
    """Validate a bounded NDC response and deduplicate without silent conflicts."""
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise ValueError("El snapshot NDC debe contener una lista 'results'")
    rows = {}
    for item in payload["results"]:
        if not isinstance(item, dict):
            raise ValueError("El catálogo contiene un registro inválido")
        code, name = item.get("product_ndc"), item.get("generic_name")
        if not isinstance(code, str) or not isinstance(name, str):
            continue
        code, name = code.strip(), " ".join(name.split())
        if not code or not name:
            continue
        if len(code) > 100 or len(name) > 255:
            raise ValueError("Catálogo excede las longitudes del esquema")
        candidate = {"codigo_fda": code, "principio_activo": name, "nivel_riesgo": None}
        if code in rows and rows[code]["principio_activo"] != name:
            raise ValueError(f"NDC repetido con nombres diferentes: {code}")
        rows[code] = candidate
    if not rows:
        raise ValueError("Catálogo sin productos válidos")
    return [rows[k] for k in sorted(rows)]


def download_catalog():
    """Retry temporary HTTP failures, never silently accept non-2xx responses."""
    retries = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
    )
    with requests.Session() as session:
        session.mount("https://", HTTPAdapter(max_retries=retries))
        response = session.get(URL, timeout=(10, 60))
        response.raise_for_status()
        payload = response.json()
    normalize(payload)  # Validate before writing any snapshot.
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()
    if args.download:
        payload = download_catalog()
        args.snapshot.parent.mkdir(parents=True, exist_ok=True)
        # Replace complete snapshots atomically rather than leaving partial JSON.
        from tempfile import NamedTemporaryFile
        temp_path = None
        try:
            with NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=args.snapshot.parent,
                prefix=".ndc-", suffix=".tmp", delete=False,
            ) as output:
                temp_path = Path(output.name)
                json.dump(payload, output, sort_keys=True, ensure_ascii=False)
                output.flush()
            temp_path.replace(args.snapshot)
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

    raw = args.snapshot.read_bytes()
    rows = normalize(json.loads(raw))
    engine = engine_from_env()
    with engine.begin() as conn:
        conn.execute(text("""INSERT INTO dim_medicamentos
            (codigo_fda, principio_activo, nivel_riesgo)
            VALUES (:codigo_fda, :principio_activo, :nivel_riesgo)
            ON CONFLICT (codigo_fda) DO UPDATE
            SET principio_activo = EXCLUDED.principio_activo"""), rows)
    print(json.dumps({
        "productos": len(rows),
        "snapshot_sha256": hashlib.sha256(raw).hexdigest(),
    }))


if __name__ == "__main__":
    main()
