# Capability registry contributor guide

The API capability registry in `api/app/capabilities.py` is the authority for capability ownership, scalar types, units, allowed values, publication handling, and compatibility adapter inputs. Catalogue model columns and admin write schemas implement that contract; they do not define it independently.

## Add or change a capability

1. Add one capability row for each owning entity. Include the stable evidence key, scalar type, unit when applicable, and allowed values for constrained fields.
2. Choose publication handling: add the categories that require the field to `required_for`, or add the `(entity, key)` pair to `PUBLICATION_OPTIONAL`. Do not leave a key in neither list or both.
3. Choose rule handling: add a direct adapter mapping under `RULE_INPUTS`, a category-selected mapping under `RULE_DERIVED_INPUTS`, or the key to `RULE_DIRECT_INPUTS` when rule preparation reads it directly. Add it to `RULE_UNUSED` only after confirming the compatibility engine does not rely on it.
4. If a grouped adapter target is added or removed, update `RULE_CONSUMED_INPUTS` to reflect the names consumed by `api/app/rules.py`.
5. Add the matching SQLAlchemy column and Pydantic admin write field. Add any needed constraints and validation. Keep model and schema scalar types aligned with the registry.
6. Associate evidence and conflict records with the same entity-scoped key. Update seeded evidence where appropriate and explain its source in the catalogue evidence documentation.
7. Run the API checks. Application startup and registry tests report missing fields, stale declarations, invalid rule mappings, and type/allowed-value disagreements.

Structured `display_configurations` use the registry's structured value type. Each entry records one source-backed simultaneous mode set as `displays` (resolution, refresh rate, and optional output connection for every external display) and an optional manufacturer-described `topology`. Do not derive entries from per-output maximums or display counts. Add the same manufacturer evidence to the capability key; leave the field null when aggregate modes/topology are undocumented.

Publication requirements and rule adapter field maps are read from the registry. Evidence and conflict writes validate their keys against that same registry, scoped to laptop or accessory ownership. No migration is needed for registry metadata by itself; adding a persisted catalogue field may require one.

## Current rule adapter notes

The laptop `usb_c_video` input is derived from the registered `usb_c_dp_version` field. Accessory `charging_output_watts` selects `usb_c_output_max_w` for chargers and `pd_pass_through_max_w` for other categories. The accessory category and host connection are read directly while preparing rule inputs. These are declared explicitly so future changes cannot silently omit their handling.
