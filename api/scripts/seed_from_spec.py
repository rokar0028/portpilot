"""Ingest device specifications from JSON files into the PortPilot catalogue.

Supports:
- Direct database upsert (default local workflow)
- REST ingestion via the protected PortPilot Admin API (--api-url)
- Dry-run validation of contributor-submitted JSON specs (--dry-run)
- Single spec file, multiple files, or entire directories
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# Ensure api directory is on sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
API_DIR = SCRIPT_DIR.parent
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.capabilities import publication_requirements, unknown_capability_keys  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import AccessoryModel, LaptopModel, SourceEvidence  # noqa: E402
from app.schemas import AccessoryWrite, LaptopWrite  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest evidence-backed laptop and accessory JSON specifications."
    )
    parser.add_argument(
        "spec_paths",
        nargs="+",
        help="Path(s) to JSON spec file(s) or directory containing JSON files.",
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default=None,
        help="Target PortPilot API base URL (e.g. http://127.0.0.1:8001). If omitted, writes directly to DB.",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="Admin API bearer token. Defaults to ADMIN_API_TOKEN environment variable.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate JSON specs against schema and capability registry without committing.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print verbose details for every processed capability and record.",
    )
    return parser.parse_args(argv)


def load_raw_specs(paths: list[str]) -> list[tuple[str, dict[str, Any]]]:
    """Load JSON records from files or directories, returning (source_path, record_dict)."""
    records: list[tuple[str, dict[str, Any]]] = []
    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")

        files = sorted(path.glob("**/*.json")) if path.is_dir() else [path]
        if not files:
            raise ValueError(f"No JSON files found in {path}")

        for file_path in files:
            with open(file_path, encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as err:
                    raise ValueError(f"Invalid JSON in {file_path}: {err}") from err

            if isinstance(data, list):
                for item in data:
                    if not isinstance(item, dict):
                        raise ValueError(f"Expected dict in list at {file_path}, got {type(item)}")
                    records.append((str(file_path), item))
            elif isinstance(data, dict):
                if "laptops" in data or "accessories" in data:
                    for laptop in data.get("laptops", []):
                        laptop_rec = dict(laptop)
                        laptop_rec["kind"] = "laptop"
                        records.append((str(file_path), laptop_rec))
                    for accessory in data.get("accessories", []):
                        acc_rec = dict(accessory)
                        acc_rec["kind"] = "accessory"
                        records.append((str(file_path), acc_rec))
                else:
                    records.append((str(file_path), data))
            else:
                raise ValueError(f"Unsupported JSON root in {file_path}: expected object or array")

    return records


def determine_entity_kind(record: dict[str, Any]) -> str:
    """Infer whether a record represents a laptop or an accessory."""
    kind = record.get("kind") or record.get("entity_type")
    if kind:
        kind_str = str(kind).strip().lower()
        if kind_str in {"laptop", "laptops"}:
            return "laptop"
        if kind_str in {"accessory", "accessories"}:
            return "accessory"
        raise ValueError(f"Unknown entity kind: {kind}")

    if "category" in record or "host_connection" in record:
        return "accessory"
    if "operating_system" in record or "usb_c_dp_version" in record:
        return "laptop"

    raise ValueError(
        f"Cannot determine device entity kind for record '{record.get('id', 'unknown')}'. "
        "Specify 'kind': 'laptop' or 'kind': 'accessory'."
    )


def normalize_evidence_list(record: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize raw seed-style or schema-style evidence into SourceEvidenceWrite dicts."""
    raw_evidence = record.get("evidence", [])
    if not raw_evidence:
        return []

    # If already a list of dicts:
    if isinstance(raw_evidence, list) and len(raw_evidence) > 0 and isinstance(raw_evidence[0], dict):
        normalized: list[dict[str, Any]] = []
        for item in raw_evidence:
            item_copy = dict(item)
            if "status" not in item_copy:
                item_copy["status"] = record.get("review_status", "verified")
            if "checked_on" not in item_copy:
                item_copy["checked_on"] = date.today().isoformat()
            elif isinstance(item_copy["checked_on"], date):
                item_copy["checked_on"] = item_copy["checked_on"].isoformat()
            normalized.append(item_copy)
        return normalized

    # Seed-style evidence: list of capability keys + top-level source metadata
    source_title = record.get("source_title")
    source_url = record.get("source_url")
    default_excerpt = record.get("excerpt", "")
    checked_on = record.get("checked_on", date.today().isoformat())
    if isinstance(checked_on, date):
        checked_on = checked_on.isoformat()
    review_status = record.get("review_status", "verified")
    evidence_excerpts = record.get("evidence_excerpts", {})

    if not source_title or not source_url:
        raise ValueError(f"Record {record.get('id')} lacks source_title or source_url for evidence.")

    normalized_list = []
    for cap_key in raw_evidence:
        excerpt = evidence_excerpts.get(cap_key, default_excerpt)
        normalized_list.append(
            {
                "id": f"{record.get('id')}:{cap_key}",
                "capability_key": cap_key,
                "title": source_title,
                "url": source_url,
                "excerpt": excerpt,
                "checked_on": checked_on,
                "status": review_status,
            }
        )
    return normalized_list


def validate_and_parse_spec(
    source_file: str, raw_record: dict[str, Any]
) -> tuple[str, LaptopWrite | AccessoryWrite]:
    """Validate a spec dictionary against capability registry and Pydantic write schemas."""
    record = dict(raw_record)
    kind = determine_entity_kind(record)
    record.pop("kind", None)
    record.pop("entity_type", None)

    device_id = record.get("id")
    if not device_id:
        raise ValueError(f"Spec in {source_file} is missing 'id'.")

    # Check unknown capability keys
    ignored_keys = {
        "id",
        "brand",
        "name",
        "review_status",
        "evidence",
        "evidence_excerpts",
        "source_title",
        "source_url",
        "excerpt",
        "checked_on",
        "change_reason",
    }
    candidate_keys = {k for k in record if k not in ignored_keys}
    unknown_keys = unknown_capability_keys(kind, candidate_keys)
    if unknown_keys:
        raise ValueError(
            f"Spec '{device_id}' contains unknown {kind} capabilities: {', '.join(unknown_keys)}"
        )

    # Check required publication fields if verified
    review_status = record.get("review_status", "draft")
    if review_status == "verified":
        category = record.get("category")
        required_caps = publication_requirements(kind, category)
        evidence_caps = set(
            ev.get("capability_key") if isinstance(ev, dict) else ev for ev in record.get("evidence", [])
        )
        for req in required_caps:
            if record.get(req) is None:
                raise ValueError(
                    f"Verified {kind} '{device_id}' is missing required publication field: '{req}'."
                )
            if req not in evidence_caps:
                raise ValueError(
                    f"Verified {kind} '{device_id}' has field '{req}' without supporting evidence citation."
                )

    # Prepare evidence list
    normalized_evidence = normalize_evidence_list(record)

    clean_payload = {
        k: v
        for k, v in record.items()
        if k not in {"source_title", "source_url", "excerpt", "evidence", "evidence_excerpts", "checked_on"}
    }
    clean_payload["evidence"] = normalized_evidence

    if kind == "laptop":
        parsed = LaptopWrite.model_validate(clean_payload)
        return "laptop", parsed
    else:
        parsed = AccessoryWrite.model_validate(clean_payload)
        return "accessory", parsed


def ingest_direct(
    parsed_specs: list[tuple[str, LaptopWrite | AccessoryWrite]], verbose: bool = False
) -> None:
    """Upsert validated specs directly to the database."""
    with SessionLocal() as session:
        for kind, spec in parsed_specs:
            spec_dict = spec.model_dump()
            evidence_items = spec_dict.pop("evidence", [])
            spec_dict.pop("change_reason", None)

            if kind == "laptop":
                model_cls = LaptopModel
                owner_field = "laptop_id"
            else:
                model_cls = AccessoryModel
                owner_field = "accessory_id"

            device_record = session.merge(model_cls(**spec_dict))

            # Upsert evidence records
            expected_evidence_ids = set()
            for ev_item in evidence_items:
                ev_id = ev_item.get("id") or f"{spec.id}:{ev_item['capability_key']}"
                expected_evidence_ids.add(ev_id)
                checked_on_val = ev_item["checked_on"]
                if isinstance(checked_on_val, str):
                    checked_on_val = date.fromisoformat(checked_on_val)

                ev_model = SourceEvidence(
                    id=ev_id,
                    capability_key=ev_item["capability_key"],
                    source_title=ev_item["title"],
                    source_url=str(ev_item["url"]),
                    excerpt=ev_item["excerpt"],
                    checked_on=checked_on_val,
                    review_status=ev_item.get("status", "verified"),
                    **{owner_field: device_record.id},
                )
                session.merge(ev_model)

            # Clean orphaned evidence for this device
            session.query(SourceEvidence).filter(
                getattr(SourceEvidence, owner_field) == device_record.id,
                SourceEvidence.id.notin_(expected_evidence_ids),
            ).delete(synchronize_session=False)

            if verbose:
                print(
                    f"  [DB] Upserted {kind} '{spec.id}' ({spec.name}) "
                    f"with {len(evidence_items)} evidence citations."
                )

        session.commit()


def ingest_via_api(
    parsed_specs: list[tuple[str, LaptopWrite | AccessoryWrite]],
    api_url: str,
    token: str | None,
    verbose: bool = False,
) -> None:
    """Send validated specs to the PortPilot Admin REST API."""
    auth_token = token or os.getenv("ADMIN_API_TOKEN")
    if not auth_token:
        raise ValueError(
            "Admin API ingestion requires an authentication token. Provide --token or set ADMIN_API_TOKEN."
        )

    base = api_url.rstrip("/")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}",
    }

    for kind, spec in parsed_specs:
        endpoint = f"{base}/admin/{'laptops' if kind == 'laptop' else 'accessories'}"
        payload_bytes = json.dumps(spec.model_dump(mode="json")).encode("utf-8")

        # Try POST first; if exists, use PUT
        req = Request(endpoint, data=payload_bytes, headers=headers, method="POST")
        try:
            with urlopen(req, timeout=15) as resp:
                if verbose:
                    print(f"  [API POST] Created {kind} '{spec.id}' ({resp.status})")
        except HTTPError as err:
            if err.code in {400, 409}:
                # Attempt PUT update
                put_url = f"{endpoint}/{spec.id}"
                put_req = Request(put_url, data=payload_bytes, headers=headers, method="PUT")
                with urlopen(put_req, timeout=15) as put_resp:
                    if verbose:
                        print(f"  [API PUT] Updated existing {kind} '{spec.id}' ({put_resp.status})")
            else:
                body = err.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"API error ingesting {kind} '{spec.id}' ({err.code}): {body}") from err
        except URLError as err:
            raise RuntimeError(f"Could not connect to PortPilot API at {api_url}: {err}") from err


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        raw_specs = load_raw_specs(args.spec_paths)
    except Exception as err:
        print(f"Error loading specs: {err}", file=sys.stderr)
        return 1

    print(f"Loaded {len(raw_specs)} device specification(s). Validating...")

    parsed_specs: list[tuple[str, LaptopWrite | AccessoryWrite]] = []
    errors: list[str] = []

    for file_path, record in raw_specs:
        rec_id = record.get("id", "unnamed")
        try:
            kind, parsed = validate_and_parse_spec(file_path, record)
            parsed_specs.append((kind, parsed))
            if args.verbose:
                print(f"  [OK] Validated {kind} '{rec_id}' from {file_path}")
        except Exception as err:
            errors.append(f"  [FAIL] [{file_path}] {rec_id}: {err}")

    if errors:
        print(f"\nValidation failed with {len(errors)} error(s):", file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    print(f"All {len(parsed_specs)} specification(s) passed validation.")

    if args.dry_run:
        print("Dry run requested. No changes were committed.")
        return 0

    try:
        if args.api_url:
            print(f"Ingesting via Admin API at {args.api_url}...")
            ingest_via_api(parsed_specs, args.api_url, args.token, verbose=args.verbose)
            print(f"Successfully ingested {len(parsed_specs)} device(s) via Admin API.")
        else:
            print("Upserting directly into PortPilot database...")
            ingest_direct(parsed_specs, verbose=args.verbose)
            print(f"Successfully ingested {len(parsed_specs)} device(s) into database.")
    except Exception as err:
        print(f"Ingestion failed: {err}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
