# Catalogue identity and evidence standard

This standard defines the requirements for model identification, regional variants, hardware revisions, and manufacturer evidence thresholds. It operationalizes Track 1 in [CONTRIBUTING.md](../CONTRIBUTING.md).

## Identity fields

- `brand` and `name` provide the readable identity.
- `model_code` is the manufacturer identifier and is required for a verified, published entry. Preserve punctuation and spelling as shown by the source.
- `region_variant` identifies a documented market or regional SKU. Leave it unknown when the source does not establish it.
- `hardware_revision` identifies a manufacturer-documented hardware revision. Do not infer a revision from a retailer listing, packaging similarity, or an undocumented suffix.
- `id` is PortPilot's stable internal key; it does not replace the manufacturer model code.

## Evidence threshold for publication

Use official manufacturer product pages, specification sheets, support pages, manuals, or regional manufacturer pages. The source must identify the exact product or variant being catalogued and support the model code and every populated capability. For each capability, retain the source URL, a short factual excerpt, and the checked date. Mark evidence `verified` only after checking that the source supports that exact field. A value copied from a different regional variant or hardware revision does not meet this threshold.

The model code and current category-specific minimum specifications must have verified evidence before publication. Other populated capability fields also require verified evidence. Unknown facts stay null; they are not inferred from similarly named models.

For multi-display limits, distinguish per-output maximums and total output counts from a simultaneous configuration. Populate `display_configurations` only when a manufacturer source states the modes supported at the same time, including any stated output connections and topology. A laptop's individual maximum and a hub's HDMI maximum do not establish aggregate bandwidth, DisplayPort lane allocation, MST behavior, or mixed-resolution combinations. If the source does not establish a combined mode, leave it unknown; the checker explains that limitation.

The seed validator enforces this model-code evidence threshold for verified records. The current seed audit found one Anker 364 hub without an established manufacturer model code; it is held as `needs_review` until resolved.

## Duplicate warning review

Admin create and edit responses may include `identity_warnings` when another record in the same device type (and accessory category) has the same normalized manufacturer code or normalized brand and model name. These are advisory candidates, not proof of a duplicate. Compare manufacturer code, region, hardware revision, and source URLs before deciding whether records are equivalent. Keep separate regional variants or revisions when manufacturer documentation distinguishes them; never merge automatically. Record unresolved identity conflicts as `needs_review` and keep the entry out of public checks until resolved.

## Adding a model

1. Confirm the exact manufacturer model code and any documented region or hardware revision.
2. Verify the source belongs to that exact identity.
3. Populate only capabilities supported by the source and attach capability-specific evidence.
4. Review any duplicate warnings against existing records.
5. Publish only when the minimum required specifications and all populated fields have verified evidence.
