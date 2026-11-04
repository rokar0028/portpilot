"""Canonical metadata for fields that can be supported by catalogue evidence."""

from dataclasses import dataclass
from typing import Literal, get_args, get_origin

from sqlalchemy import JSON, Boolean, Integer, String

EntityKind = Literal["laptop", "accessory"]
ValueType = Literal["string", "integer", "boolean", "display_configurations"]


@dataclass(frozen=True)
class Capability:
    key: str
    entity: EntityKind
    value_type: ValueType
    unit: str | None = None
    required_for: tuple[str, ...] = ()
    allowed_values: tuple[str, ...] = ()


_CAPABILITY_ROWS = (
    ("model_code", "laptop", "string", None, ("laptop",)),
    ("region_variant", "laptop", "string", None),
    ("hardware_revision", "laptop", "string", None),
    ("operating_system", "laptop", "string", None),
    ("usb_c_port_count", "laptop", "integer", "ports", ("laptop",)),
    ("usb_c_data_rate_gbps", "laptop", "integer", "Gb/s"),
    ("usb_c_video_supported", "laptop", "boolean", None),
    ("usb_c_dp_version", "laptop", "string", None),
    ("usb_c_pd_input_min_w", "laptop", "integer", "W"),
    ("usb_c_pd_input_max_w", "laptop", "integer", "W"),
    ("hdmi_version", "laptop", "string", None),
    ("hdmi_max_resolution", "laptop", "string", None),
    ("hdmi_max_refresh_hz", "laptop", "integer", "Hz"),
    ("maximum_external_displays", "laptop", "integer", "displays"),
    ("usb_c_max_resolution", "laptop", "string", None),
    ("usb_c_max_refresh_hz", "laptop", "integer", "Hz"),
    ("display_configurations", "laptop", "display_configurations", None),
    (
        "model_code",
        "accessory",
        "string",
        None,
        ("usb_c_hub", "usb_c_dock", "usb_c_charger", "portable_monitor", "external_display"),
    ),
    ("region_variant", "accessory", "string", None),
    ("hardware_revision", "accessory", "string", None),
    (
        "category",
        "accessory",
        "string",
        None,
        ("usb_c_hub", "usb_c_dock", "usb_c_charger", "portable_monitor", "external_display"),
        ("usb_c_hub", "usb_c_dock", "usb_c_charger", "portable_monitor", "external_display"),
    ),
    (
        "host_connection",
        "accessory",
        "string",
        None,
        ("usb_c_hub", "usb_c_dock", "usb_c_charger", "portable_monitor", "external_display"),
    ),
    ("requires_usb_c_dp_alt_mode", "accessory", "boolean", None, ("usb_c_hub", "usb_c_dock")),
    ("hdmi_port_count", "accessory", "integer", "ports", ("usb_c_hub", "usb_c_dock")),
    (
        "hdmi_max_resolution",
        "accessory",
        "string",
        None,
        ("portable_monitor", "external_display", "usb_c_hub", "usb_c_dock"),
    ),
    (
        "hdmi_max_refresh_hz",
        "accessory",
        "integer",
        "Hz",
        ("portable_monitor", "external_display", "usb_c_hub", "usb_c_dock"),
    ),
    ("pd_input_max_w", "accessory", "integer", "W"),
    ("pd_pass_through_max_w", "accessory", "integer", "W"),
    ("usb_c_output_max_w", "accessory", "integer", "W", ("usb_c_charger",)),
    ("usb_a_port_count", "accessory", "integer", "ports"),
    ("ethernet_max_gbps", "accessory", "integer", "Gb/s"),
    ("display_configurations", "accessory", "display_configurations", None),
)

_RULE_INPUTS = {
    "laptop": {
        "ports": {
            "usb_c_port_count": "usb_c_port_count",
            "usb_c_video_supported": "usb_c_video_supported",
            "usb_c_pd_input_min_w": "usb_c_pd_input_min_w",
            "usb_c_pd_input_max_w": "usb_c_pd_input_max_w",
            "maximum_external_displays": "maximum_external_displays",
            "usb_c_max_resolution": "usb_c_max_resolution",
            "usb_c_max_refresh_hz": "usb_c_max_refresh_hz",
            "hdmi_max_resolution": "hdmi_max_resolution",
            "hdmi_max_refresh_hz": "hdmi_max_refresh_hz",
            "display_configurations": "display_configurations",
        }
    },
    "accessory": {
        "requirements": {"host_usb_c_video": "requires_usb_c_dp_alt_mode"},
        "outputs": {
            "display_count": "hdmi_port_count",
            "hdmi_max_resolution": "hdmi_max_resolution",
            "hdmi_max_refresh_hz": "hdmi_max_refresh_hz",
            "display_configurations": "display_configurations",
        },
    },
}

# Fields intentionally not used by the current compatibility engine. Keep this
# list explicit so a newly added capability cannot silently miss rule review.
RULE_UNUSED = {
    ("laptop", key)
    for key in (
        "model_code",
        "region_variant",
        "hardware_revision",
        "usb_c_data_rate_gbps",
        "hdmi_version",
    )
} | {
    ("accessory", key)
    for key in (
        "model_code",
        "region_variant",
        "hardware_revision",
        "usb_a_port_count",
        "ethernet_max_gbps",
    )
}

# Adapter names are an internal contract with rules.py. This inventory makes
# it possible to catch a rule that begins reading an unmapped adapter field.
RULE_CONSUMED_INPUTS = {
    "laptop": {
        "ports": {
            "usb_c_port_count",
            "usb_c_video_supported",
            "usb_c_pd_input_min_w",
            "usb_c_pd_input_max_w",
            "maximum_external_displays",
            "usb_c_max_resolution",
            "usb_c_max_refresh_hz",
            "hdmi_max_resolution",
            "hdmi_max_refresh_hz",
            "display_configurations",
        }
    },
    "accessory": {
        "requirements": {"host_usb_c_video"},
        "outputs": {
            "display_count",
            "hdmi_max_resolution",
            "hdmi_max_refresh_hz",
            "display_configurations",
            "charging_output_watts",
        },
    },
}

PUBLICATION_OPTIONAL = {
    ("laptop", key)
    for key in (
        "region_variant",
        "hardware_revision",
        "operating_system",
        "usb_c_data_rate_gbps",
        "usb_c_video_supported",
        "usb_c_dp_version",
        "usb_c_pd_input_min_w",
        "usb_c_pd_input_max_w",
        "hdmi_version",
        "hdmi_max_resolution",
        "hdmi_max_refresh_hz",
        "maximum_external_displays",
        "usb_c_max_resolution",
        "usb_c_max_refresh_hz",
        "display_configurations",
    )
} | {
    ("accessory", key)
    for key in (
        "region_variant",
        "hardware_revision",
        "requires_usb_c_dp_alt_mode",
        "hdmi_port_count",
        "hdmi_max_resolution",
        "hdmi_max_refresh_hz",
        "pd_input_max_w",
        "pd_pass_through_max_w",
        "usb_a_port_count",
        "ethernet_max_gbps",
        "display_configurations",
    )
}

# Optional only for the listed types when a capability is required for other
# types. This captures fields such as HDMI outputs that are required for hubs
# but irrelevant to charger publication.
PUBLICATION_OPTIONAL_FOR = {
    ("accessory", "requires_usb_c_dp_alt_mode"): ("usb_c_charger", "portable_monitor", "external_display"),
    ("accessory", "hdmi_port_count"): ("usb_c_charger", "portable_monitor", "external_display"),
    ("accessory", "hdmi_max_resolution"): ("usb_c_charger",),
    ("accessory", "hdmi_max_refresh_hz"): ("usb_c_charger",),
    ("accessory", "usb_c_output_max_w"): ("usb_c_hub", "usb_c_dock", "portable_monitor", "external_display"),
}

# A derived input depends on the device category and therefore has a short
# adapter function in main.py. Its source capabilities still belong to this registry.
RULE_DERIVED_INPUTS = {
    "accessory": {
        "outputs": {
            "charging_output_watts": {
                "usb_c_charger": "usb_c_output_max_w",
                "default": "pd_pass_through_max_w",
            }
        }
    }
}

# These fields are read directly by rule preparation/control flow, outside the
# grouped adapter dictionaries (for example host connection and category).
RULE_DIRECT_INPUTS = {
    ("laptop", "usb_c_dp_version"),
    ("laptop", "operating_system"),
    ("accessory", "category"),
    ("accessory", "host_connection"),
    ("accessory", "pd_input_max_w"),
}

CAPABILITIES = {
    (entity, row[0]): Capability(
        row[0], entity, row[2], row[3], row[4] if len(row) > 4 else (), row[5] if len(row) > 5 else ()
    )
    for row in _CAPABILITY_ROWS
    for entity in (row[1],)
}

RULE_INPUTS = _RULE_INPUTS


def validate_registry(
    models: dict[str, type], schemas: dict[str, type], *, consumed_inputs: dict | None = None
) -> None:
    """Fail at startup when registry, persistence, API, or rules drift apart."""
    validate_registry_fields(
        {column.name for column in models["laptop"].__table__.columns},
        {column.name for column in models["accessory"].__table__.columns},
        {name for name in schemas["laptop"].model_fields},
        {name for name in schemas["accessory"].model_fields},
    )
    validate_registry_types(models, schemas)
    all_keys = set(CAPABILITIES)
    accessory_categories = set(CAPABILITIES[("accessory", "category")].allowed_values)
    publication_types = {"laptop": {"laptop"}, "accessory": accessory_categories}
    optional_for = {key: set(publication_types[key[0]]) for key in PUBLICATION_OPTIONAL}
    optional_for.update({key: set(types) for key, types in PUBLICATION_OPTIONAL_FOR.items()})
    invalid_publication_declarations = set(optional_for) - all_keys
    unhandled_publication = {
        (entity, capability.key, publication_type)
        for (entity, _), capability in CAPABILITIES.items()
        for publication_type in publication_types[entity]
        if publication_type not in capability.required_for
        and publication_type not in optional_for.get((entity, capability.key), set())
    }
    conflicting_publication = {
        (entity, capability.key, publication_type)
        for (entity, _), capability in CAPABILITIES.items()
        for publication_type in capability.required_for
        if publication_type in optional_for.get((entity, capability.key), set())
    }
    if unhandled_publication or invalid_publication_declarations or conflicting_publication:
        details = sorted(unhandled_publication | invalid_publication_declarations | conflicting_publication)
        raise ValueError(f"Capability publication handling is incomplete or stale: {details}")
    invalid_publication_types = sorted(
        (entity, capability.key, publication_type)
        for (entity, _), capability in CAPABILITIES.items()
        for publication_type in capability.required_for
        if (entity == "laptop" and publication_type != "laptop")
        or (entity == "accessory" and publication_type not in accessory_categories)
    )
    if invalid_publication_types:
        raise ValueError(f"Capability has invalid publication types: {invalid_publication_types}")

    mapped: set[tuple[str, str]] = set()
    for entity, groups in RULE_INPUTS.items():
        for group, fields in groups.items():
            for target, source in fields.items():
                key = (entity, source)
                if key not in CAPABILITIES:
                    raise ValueError(
                        f"Rule adapter {entity}.{group}.{target} uses unregistered capability {source!r}"
                    )
                mapped.add(key)
    for entity, groups in RULE_DERIVED_INPUTS.items():
        for group, targets in groups.items():
            for target, sources in targets.items():
                for source in sources.values():
                    if (entity, source) not in CAPABILITIES:
                        raise ValueError(
                            f"Derived adapter {entity}.{group}.{target} uses unregistered key {source!r}"
                        )
                    mapped.add((entity, source))
    mapped.update(RULE_DIRECT_INPUTS)
    unhandled_rules = all_keys - mapped - RULE_UNUSED
    stale_rules = RULE_UNUSED - all_keys
    if unhandled_rules or stale_rules or mapped & RULE_UNUSED:
        raise ValueError(
            "Capability rule handling is incomplete, overlapping, or stale: "
            f"{sorted(unhandled_rules | stale_rules | (mapped & RULE_UNUSED))}"
        )

    expected = RULE_CONSUMED_INPUTS if consumed_inputs is None else consumed_inputs
    for entity, groups in expected.items():
        for group, targets in groups.items():
            mapped_targets = set(RULE_INPUTS.get(entity, {}).get(group, {})) | set(
                RULE_DERIVED_INPUTS.get(entity, {}).get(group, {})
            )
            missing = set(targets) - mapped_targets
            stale = mapped_targets - set(targets)
            if missing or stale:
                raise ValueError(
                    f"Rule adapter inputs disagree for {entity}.{group}: "
                    f"unmapped={sorted(missing)}, unconsumed={sorted(stale)}"
                )


def unknown_capability_keys(entity: EntityKind, keys: set[str]) -> list[str]:
    """Return sorted evidence keys not registered for the specified entity."""
    return sorted(key for key in keys if (entity, key) not in CAPABILITIES)


def publication_requirements(entity: EntityKind, category: str | None = None) -> tuple[str, ...]:
    """Return required capability keys for a publication type."""
    return tuple(
        capability.key
        for (owner, _), capability in CAPABILITIES.items()
        if owner == entity
        and (
            (entity == "laptop" and "laptop" in capability.required_for)
            or (entity == "accessory" and category in capability.required_for)
        )
    )


def validate_registry_fields(
    laptop_fields: set[str],
    accessory_fields: set[str],
    laptop_schema_fields: set[str] | None = None,
    accessory_schema_fields: set[str] | None = None,
) -> None:
    """Raise when an evidence-capable model field lacks registry metadata."""
    registered = {
        "laptop": {key for entity, key in CAPABILITIES if entity == "laptop"},
        "accessory": {key for entity, key in CAPABILITIES if entity == "accessory"},
    }
    for entity, actual in (("laptop", laptop_fields), ("accessory", accessory_fields)):
        ignored = {"id", "brand", "name", "review_status"}
        missing = sorted(actual - ignored - registered[entity])
        if missing:
            raise ValueError(f"Unregistered {entity} capability fields: {', '.join(missing)}")
        orphaned = sorted(registered[entity] - actual)
        if orphaned:
            raise ValueError(f"Registry {entity} capabilities missing model fields: {', '.join(orphaned)}")
    for entity, actual, schema_fields in (
        ("laptop", laptop_fields, laptop_schema_fields),
        ("accessory", accessory_fields, accessory_schema_fields),
    ):
        if schema_fields is not None:
            missing = sorted((actual - {"id", "review_status"}) - schema_fields)
            if missing:
                raise ValueError(f"Missing {entity} write-schema fields: {', '.join(missing)}")


def validate_registry_types(models: dict[str, type], schemas: dict[str, type]) -> None:
    """Ensure registry scalar types agree with persisted columns and API write schemas."""
    sql_types = {
        "string": String,
        "integer": Integer,
        "boolean": Boolean,
        "display_configurations": JSON,
    }
    python_types = {"string": str, "integer": int, "boolean": bool, "display_configurations": list}
    for (entity, key), capability in CAPABILITIES.items():
        column = models[entity].__table__.columns[key]
        if not isinstance(column.type, sql_types[capability.value_type]):
            raise ValueError(f"{entity}.{key} SQL type disagrees with capability registry")
        annotation = schemas[entity].model_fields[key].annotation
        accepted_types = {arg for arg in get_args(annotation) if arg is not type(None)}
        if get_origin(annotation) is None:
            accepted_types = {annotation}
        elif get_origin(annotation) is Literal:
            accepted_types = {type(arg) for arg in accepted_types}
        if capability.value_type == "display_configurations":
            list_types = {arg for arg in get_args(annotation) if get_origin(arg) is list}
            type_matches = bool(list_types)
        else:
            type_matches = python_types[capability.value_type] in accepted_types
        if not type_matches:
            raise ValueError(f"{entity}.{key} schema type disagrees with capability registry")
        if capability.allowed_values:
            values = set(get_args(annotation)) if get_origin(annotation) is Literal else set()
            if values != set(capability.allowed_values):
                raise ValueError(f"{entity}.{key} schema allowed values disagree with capability registry")


def rule_fields(entity: EntityKind, group: str) -> dict[str, str]:
    """Return rule input names mapped to catalogue field names."""
    return RULE_INPUTS[entity][group]


def derived_rule_fields(entity: EntityKind, group: str, selector: str) -> dict[str, str]:
    """Return category-selected catalogue sources for derived rule inputs."""
    return {
        target: sources.get(selector, sources["default"])
        for target, sources in RULE_DERIVED_INPUTS.get(entity, {}).get(group, {}).items()
    }
