# Source review playbook

This playbook guides reviewers and contributors when selecting manufacturer evidence, resolving conflicting specifications, rechecking stale sources, and recording catalogue corrections. It operationalizes Track 1 in [CONTRIBUTING.md](../CONTRIBUTING.md) and aligns with [Catalogue Identity and Evidence Standard](catalogue-identity-and-evidence.md).

## Selecting a source

Prefer an official manufacturer manual, product specification page, support page, or region-specific manufacturer page. Verify that it identifies the exact model code, region, and hardware revision being reviewed. Record the URL, a short factual excerpt, capability key, and checked date for every populated capability. Use retailer and community sources only as leads; they do not establish a published capability.

## Resolving conflicting claims

1. Open an admin evidence conflict with both values, source URLs, and source-quality classifications (`manufacturer_primary`, `manufacturer_secondary`, or `other`). This automatically places the device in `needs_review` and removes it from public checks.
2. Compare source scope and recency, exact model/region/revision coverage, and whether each claim addresses the same capability and conditions.
3. Resolve the conflict by selecting one of the recorded claims and recording the reviewer and rationale. The conflict record remains in history.
4. Recheck the selected claim against the exact manufacturer source and record the outcome. An open conflict blocks marking evidence verified.
5. Explicitly update the catalogue value and evidence with a correction reason. Re-publication remains a separate reviewed action; resolving a conflict never republishes automatically.

If neither claim can be established, leave the value unknown or keep the device in `needs_review`. Do not average claims or substitute information from a similar model.

## Rechecking stale evidence

Use the stale-evidence queue with an explicit age threshold. Open the source and confirm that it still applies to the exact device identity and capability. Record the outcome, checked date, concise note, and reviewer. A failed or uncertain recheck marks the evidence and device `needs_review`; a successful recheck does not override another open conflict.

## Recording corrections

Every changed catalogue field or evidence record requires a `change_reason`. The API records previous and new values, evidence record references, actor (`X-Admin-Actor`, default `admin`), and timestamp. Correction history is append-only. Never edit or delete earlier correction records to rewrite the review trail.
