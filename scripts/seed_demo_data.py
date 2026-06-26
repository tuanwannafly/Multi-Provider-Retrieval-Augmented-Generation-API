"""Seed demo collections by uploading the sample files to a running API.

Usage (inside the api container or against a local server):
    python scripts/seed_demo_data.py
    BASE_URL=http://localhost:8000 python scripts/seed_demo_data.py

Maps:
    examples/intro_to_ml.pdf        -> collection "ml-basics"
    examples/deep_learning_basics.pdf -> collection "dl-intro"
    examples/nlp_fundamentals.pdf    -> collection "nlp-basics"
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    import httpx
except ImportError as exc:  # pragma: no cover
    raise SystemExit("httpx is required: pip install httpx") from exc

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"

SEED_MAP = {
    "intro_to_ml.pdf": "ml-basics",
    "deep_learning_basics.pdf": "dl-intro",
    "nlp_fundamentals.pdf": "nlp-basics",
}


def main() -> int:
    print(f"Seeding demo data against {BASE_URL}")
    exit_code = 0
    for filename, collection in SEED_MAP.items():
        path = EXAMPLES_DIR / filename
        if not path.exists():
            print(f"  ! missing {path}; run generate_sample_pdfs.py first")
            exit_code = 1
            continue
        with path.open("rb") as fh:
            try:
                resp = httpx.post(
                    f"{BASE_URL}/documents/upload",
                    data={"collection": collection},
                    files={"file": (filename, fh, "application/pdf")},
                    timeout=120.0,
                )
            except httpx.HTTPError as exc:
                print(f"  ! {filename}: request failed: {exc}")
                exit_code = 1
                continue
        if resp.status_code in (200, 409):
            print(
                f"  + {filename} -> {collection}: "
                f"{resp.json().get('chunks_created', 'exists')}"
            )
        else:
            print(f"  ! {filename}: {resp.status_code} {resp.text}")
            exit_code = 1
    print("Seed complete.")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
