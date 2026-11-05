"""Audit evidence freshness across published devices in the PortPilot catalogue.

Queries verified manufacturer evidence and flags records whose checked_on date
exceeds the maximum age threshold (default 180 days).

Can be run:
- Directly against database: `python scripts/check_evidence_staleness.py`
- Against live preview: `python scripts/check_evidence_staleness.py --api-url http://... --token ...`
- In CI workflows to enforce that published evidence is audited periodically.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# Ensure api directory is on sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
API_DIR = SCRIPT_DIR.parent
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import selectinload  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models import SourceEvidence  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit PortPilot catalogue evidence for staleness.")
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=180,
        help="Maximum allowed age for verified evidence citations before flagging (default: 180 days).",
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default=None,
        help="Target PortPilot API base URL (e.g. http://127.0.0.1:8001). If omitted, queries local DB.",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="Admin API bearer token for HTTP audit. Defaults to ADMIN_API_TOKEN env var.",
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Exit with code 0 even if stale evidence records are found.",
    )
    return parser.parse_args(argv)


def query_stale_direct(max_age_days: int) -> list[dict]:
    cutoff_date = date.today() - timedelta(days=max_age_days)
    today = date.today()
    results = []
    with SessionLocal() as session:
        evidences = session.scalars(
            select(SourceEvidence)
            .where(
                SourceEvidence.review_status == "verified",
                SourceEvidence.checked_on < cutoff_date,
            )
            .options(
                selectinload(SourceEvidence.laptop),
                selectinload(SourceEvidence.accessory),
            )
            .order_by(SourceEvidence.checked_on.asc())
        ).all()

        for ev in evidences:
            if ev.laptop:
                entity_type = "laptop"
                device_id = ev.laptop_id or ""
                device_name = ev.laptop.name
            else:
                entity_type = "accessory"
                device_id = ev.accessory_id or ""
                device_name = ev.accessory.name if ev.accessory else ""

            results.append(
                {
                    "id": ev.id,
                    "entity_type": entity_type,
                    "device_id": device_id,
                    "device_name": device_name,
                    "capability_key": ev.capability_key,
                    "source_title": ev.source_title,
                    "source_url": ev.source_url,
                    "checked_on": ev.checked_on.isoformat(),
                    "age_days": (today - ev.checked_on).days,
                }
            )
    return results


def query_stale_api(api_url: str, token: str | None, max_age_days: int) -> list[dict]:
    auth_token = token or os.getenv("ADMIN_API_TOKEN")
    if not auth_token:
        raise ValueError("HTTP audit requires --token or ADMIN_API_TOKEN environment variable.")

    url = f"{api_url.rstrip('/')}/admin/evidence/stale?max_age_days={max_age_days}"
    headers = {"Authorization": f"Bearer {auth_token}"}
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("stale_items", [])
    except (HTTPError, URLError) as err:
        raise RuntimeError(f"Failed to query stale evidence from API: {err}") from err


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    print(f"Auditing evidence freshness (threshold: {args.max_age_days} days)...")

    try:
        if args.api_url:
            stale_items = query_stale_api(args.api_url, args.token, args.max_age_days)
        else:
            stale_items = query_stale_direct(args.max_age_days)
    except Exception as err:
        print(f"Audit error: {err}", file=sys.stderr)
        return 1

    if not stale_items:
        print(f"All verified catalogue evidence is up to date (< {args.max_age_days} days old).")
        return 0

    print(f"\nWARNING: Found {len(stale_items)} verified evidence record(s) > {args.max_age_days} days old:")
    print("-" * 90)
    print(f"{'Age':<8} {'Entity':<10} {'Device ID':<30} {'Capability':<25} {'Checked On':<12}")
    print("-" * 90)
    for item in stale_items:
        print(
            f"{item['age_days']}d{'':<4} "
            f"{item['entity_type']:<10} "
            f"{item['device_id']:<30} "
            f"{item['capability_key']:<25} "
            f"{item['checked_on']:<12}"
        )
    print("-" * 90)
    print("Action required: Recheck manufacturer sources and update checked_on dates in catalogue.\n")

    return 0 if args.warn_only else 1


if __name__ == "__main__":
    sys.exit(main())
