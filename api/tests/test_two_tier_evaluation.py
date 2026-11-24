from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.rules import evaluate
from app.schemas import CheckRequest, SetupRequest
from app.seed import ACCESSORIES, LAPTOPS, seed


def test_verified_device_returns_verified_tier():
    with SessionLocal():
        seed()

    client = TestClient(app)
    response = client.post(
        "/checks",
        json={
            "laptop_id": "lenovo-ideapad-slim-3-14irh10r",
            "accessory_id": "anker-nano-hub-7in1-a83d2",
            "setup": {
                "external_displays": 1,
                "resolution": "1920x1080",
                "refresh_rate_hz": 60,
                "laptop_charging": True,
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "compatible"
    assert data["evaluation_tier"] == "verified"
    assert "supported by the available specifications" in data["summary"]


def test_standard_protocol_profiles_return_theoretical_tier():
    with SessionLocal():
        seed()

    client = TestClient(app)
    response = client.post(
        "/checks",
        json={
            "laptop_id": "protocol-thunderbolt-4-host",
            "accessory_id": "protocol-thunderbolt-4-dock",
            "setup": {
                "external_displays": 2,
                "resolution": "3840x2160",
                "refresh_rate_hz": 60,
                "laptop_charging": True,
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] in {"compatible", "compatible_with_limits"}
    assert data["evaluation_tier"] == "theoretical"
    assert "theoretically supported" in data["summary"]


def test_standard_protocol_macos_mst_evaluates_with_constraints():
    with SessionLocal():
        seed()

    client = TestClient(app)
    response = client.post(
        "/checks",
        json={
            "laptop_id": "protocol-apple-silicon-base",
            "accessory_id": "protocol-usbc-dual-mst-dock",
            "setup": {
                "external_displays": 2,
                "resolution": "1920x1080",
                "refresh_rate_hz": 60,
                "laptop_charging": True,
                "display_topology": "extended",
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "incompatible"
    assert data["evaluation_tier"] == "theoretical"
    mst_check = next(c for c in data["requirements"] if c["name"] == "Display topology (MST)")
    assert mst_check["status"] == "failed"
    assert "macOS does not support DisplayPort Multi-Stream Transport" in mst_check["detail"]


def test_rule_evaluates_explicit_request_tier():
    laptop = next(e for e in LAPTOPS if e["id"] == "lenovo-ideapad-slim-3-14irh10r")
    accessory = next(e for e in ACCESSORIES if e["id"] == "anker-nano-hub-7in1-a83d2")

    from app.main import accessory_rule_record, laptop_rule_record
    from app.models import AccessoryModel, LaptopModel

    l_model = LaptopModel(
        **{
            k: v
            for k, v in laptop.items()
            if k not in {"source_title", "source_url", "excerpt", "evidence", "evidence_excerpts"}
        }
    )
    a_model = AccessoryModel(
        **{
            k: v
            for k, v in accessory.items()
            if k not in {"source_title", "source_url", "excerpt", "evidence", "evidence_excerpts"}
        }
    )

    req = CheckRequest(
        laptop_id=laptop["id"],
        accessory_id=accessory["id"],
        setup=SetupRequest(
            external_displays=1, resolution="1920x1080", refresh_rate_hz=60, laptop_charging=True
        ),
        evaluation_tier="theoretical",
    )
    result = evaluate(req, laptop_rule_record(l_model), accessory_rule_record(a_model))
    assert result["evaluation_tier"] == "theoretical"
    assert "theoretically supported" in result["summary"]
