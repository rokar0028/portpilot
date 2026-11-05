import pytest

from app import capabilities
from app.models import AccessoryModel, LaptopModel
from app.schemas import AccessoryWrite, LaptopWrite

MODELS = {"laptop": LaptopModel, "accessory": AccessoryModel}
SCHEMAS = {"laptop": LaptopWrite, "accessory": AccessoryWrite}


def test_registry_is_consistent_across_models_schemas_publication_and_rules() -> None:
    capabilities.validate_registry(MODELS, SCHEMAS)
    assert capabilities.publication_requirements("laptop") == ("model_code", "usb_c_port_count")
    assert set(capabilities.publication_requirements("accessory", "usb_c_charger")) == {
        "model_code",
        "category",
        "host_connection",
        "usb_c_output_max_w",
    }
    assert ("accessory", "displaylink_supported") in capabilities.CAPABILITIES
    assert ("accessory", "displaylink_supported") in capabilities.PUBLICATION_OPTIONAL


def test_evidence_keys_are_scoped_to_registered_entity() -> None:
    assert capabilities.unknown_capability_keys("laptop", {"usb_c_port_count", "not_a_field"}) == [
        "not_a_field"
    ]
    assert capabilities.unknown_capability_keys("accessory", {"usb_c_port_count"}) == ["usb_c_port_count"]


def test_unhandled_capability_fails_with_its_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(capabilities, "RULE_UNUSED", capabilities.RULE_UNUSED - {("laptop", "model_code")})
    with pytest.raises(ValueError, match="rule handling.*model_code"):
        capabilities.validate_registry(MODELS, SCHEMAS)


def test_rule_input_not_consumed_by_engine_fails_clearly() -> None:
    consumed = {"laptop": {"ports": {"future_rule_input"}}}
    with pytest.raises(ValueError, match="unmapped=.*future_rule_input"):
        capabilities.validate_registry(MODELS, SCHEMAS, consumed_inputs=consumed)


def test_write_schema_missing_model_field_fails_clearly() -> None:
    with pytest.raises(ValueError, match="Missing laptop write-schema fields: usb_c_port_count"):
        capabilities.validate_registry_fields(
            {column.name for column in LaptopModel.__table__.columns},
            {column.name for column in AccessoryModel.__table__.columns},
            set(LaptopWrite.model_fields) - {"usb_c_port_count"},
            set(AccessoryWrite.model_fields),
        )
