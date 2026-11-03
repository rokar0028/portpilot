import pytest

from app.rules import evaluate
from app.schemas import CheckRequest


def records() -> tuple[dict, dict]:
    laptop = {
        "ports": {
            "usb_c_port_count": 1,
            "usb_c_video_supported": True,
            "usb_c_pd_input_min_w": 45,
            "usb_c_pd_input_max_w": 65,
            "maximum_external_displays": 2,
            "usb_c_max_resolution": "4K",
            "usb_c_max_refresh_hz": 60,
            "hdmi_max_resolution": "4K",
            "hdmi_max_refresh_hz": 30,
        },
        "evidence": [],
    }
    accessory = {
        "host_connection": "USB-C",
        "requirements": {"host_usb_c_video": True},
        "outputs": {
            "display_count": 2,
            "hdmi_max_resolution": "3840x2160",
            "hdmi_max_refresh_hz": 60,
            "charging_output_watts": 65,
        },
        "evidence": [],
    }
    return laptop, accessory


def check(laptop: dict, accessory: dict, **setup: object) -> dict:
    request = CheckRequest(
        laptop_id="laptop",
        accessory_id="hub",
        setup={"external_displays": 1, "resolution": "1920x1080", "refresh_rate_hz": 60, **setup},
    )
    return evaluate(request, laptop, accessory)


def test_supported_setup_is_compatible() -> None:
    laptop, accessory = records()
    assert check(laptop, accessory)["verdict"] == "compatible"


def test_charging_below_laptop_max_is_reported_as_a_limit() -> None:
    laptop, accessory = records()
    accessory["outputs"]["charging_output_watts"] = 50
    result = check(laptop, accessory)
    assert result["verdict"] == "compatible_with_limits"
    assert result["limits"]


def test_explicitly_unsupported_video_is_incompatible() -> None:
    laptop, accessory = records()
    laptop["ports"]["usb_c_video_supported"] = False
    assert check(laptop, accessory)["verdict"] == "incompatible"


def test_unknown_required_capability_is_insufficient_data() -> None:
    laptop, accessory = records()
    laptop["ports"]["maximum_external_displays"] = None
    assert check(laptop, accessory)["verdict"] == "insufficient_data"


def test_unknown_video_path_does_not_assume_hdmi() -> None:
    laptop, accessory = records()
    accessory["requirements"]["host_usb_c_video"] = None
    result = check(laptop, accessory)
    assert result["verdict"] == "insufficient_data"
    assert all(item["status"] != "failed" for item in result["requirements"])


def test_exceeding_documented_refresh_rate_is_incompatible() -> None:
    laptop, accessory = records()
    result = check(laptop, accessory, resolution="3840x2160", refresh_rate_hz=120)
    assert result["verdict"] == "incompatible"


@pytest.mark.parametrize(
    ("setup", "expected"),
    [
        ({"resolution": "3840x2160", "refresh_rate_hz": 60}, "compatible"),
        ({"resolution": "3840x2160", "refresh_rate_hz": 61}, "incompatible"),
        ({"resolution": "1920x1080", "refresh_rate_hz": 24}, "compatible"),
        ({"resolution": "1280x720", "refresh_rate_hz": 60}, "compatible"),
        ({"resolution": "4096x2160", "refresh_rate_hz": 60}, "incompatible"),
        ({"resolution": "1920x1200", "refresh_rate_hz": 60}, "compatible"),
        ({"external_displays": 2}, "insufficient_data"),
        ({"external_displays": 3}, "incompatible"),
        ({"external_displays": 0}, "compatible"),
        ({"laptop_charging": False}, "compatible"),
    ],
)
def test_documented_mode_counts_and_optional_features(setup: dict, expected: str) -> None:
    laptop, accessory = records()
    assert check(laptop, accessory, **setup)["verdict"] == expected


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (lambda laptop, accessory: laptop["ports"].update(usb_c_port_count=0), "incompatible"),
        (lambda laptop, accessory: laptop["ports"].update(usb_c_port_count=None), "insufficient_data"),
        (lambda laptop, accessory: laptop["ports"].update(usb_c_video_supported=None), "insufficient_data"),
        (lambda laptop, accessory: laptop["ports"].update(usb_c_max_refresh_hz=None), "insufficient_data"),
        (lambda laptop, accessory: laptop["ports"].update(maximum_external_displays=0), "incompatible"),
        (lambda laptop, accessory: accessory["outputs"].update(display_count=0), "incompatible"),
        (lambda laptop, accessory: accessory["outputs"].update(display_count=None), "insufficient_data"),
        (
            lambda laptop, accessory: accessory["outputs"].update(hdmi_max_resolution=None),
            "insufficient_data",
        ),
        (lambda laptop, accessory: accessory["outputs"].update(hdmi_max_refresh_hz=30), "incompatible"),
        (lambda laptop, accessory: accessory["outputs"].update(charging_output_watts=44), "incompatible"),
        (
            lambda laptop, accessory: accessory["outputs"].update(charging_output_watts=None),
            "insufficient_data",
        ),
        (lambda laptop, accessory: accessory.update(host_connection=None), "insufficient_data"),
    ],
)
def test_missing_and_unsupported_catalogue_facts(mutation, expected: str) -> None:
    laptop, accessory = records()
    mutation(laptop, accessory)
    assert check(laptop, accessory)["verdict"] == expected


def test_unmodeled_video_path_does_not_assume_laptop_hdmi() -> None:
    laptop, accessory = records()
    accessory["requirements"]["host_usb_c_video"] = False
    laptop["ports"]["hdmi_max_refresh_hz"] = 60
    assert check(laptop, accessory)["verdict"] == "insufficient_data"


def test_charging_output_equal_to_laptop_minimum_is_limited() -> None:
    laptop, accessory = records()
    accessory["outputs"]["charging_output_watts"] = 45
    result = check(laptop, accessory)
    assert result["verdict"] == "compatible_with_limits"


def test_incompatible_precedes_unknown_in_verdict() -> None:
    laptop, accessory = records()
    laptop["ports"].update(usb_c_video_supported=False, maximum_external_displays=None)
    assert check(laptop, accessory)["verdict"] == "incompatible"


def test_unmodeled_resolution_is_unknown_not_a_failure() -> None:
    laptop, accessory = records()
    result = check(laptop, accessory, resolution="custom-mode")
    assert result["verdict"] == "insufficient_data"


@pytest.mark.parametrize(
    ("maximum_resolution", "maximum_refresh", "requested_resolution", "requested_refresh", "expected"),
    [
        ("3840x2160", 60, "4K", 60, True),
        ("3840x2160", 60, "UHD", 60, True),
        ("1920x1080", 60, "1080p", 60, True),
        ("2560x1440", 144, "1440p", 144, True),
        ("1920x1080", 60, "2560x1440", 60, False),
        ("3840x2160", 60, "3840x2160", 61, False),
        ("unknown", 60, "1920x1080", 60, None),
        ("3840x2160", None, "1920x1080", 60, None),
    ],
)
def test_display_mode_aliases_and_boundaries(
    maximum_resolution: str,
    maximum_refresh: int | None,
    requested_resolution: str,
    requested_refresh: int,
    expected: bool | None,
) -> None:
    from app.rules import _mode_at_least

    assert (
        _mode_at_least(maximum_resolution, maximum_refresh, requested_resolution, requested_refresh)
        is expected
    )


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (lambda laptop, accessory: laptop["ports"].update(maximum_external_displays=1), "incompatible"),
        (lambda laptop, accessory: accessory["outputs"].update(display_count=1), "incompatible"),
        (
            lambda laptop, accessory: accessory["requirements"].update(host_usb_c_video=False),
            "insufficient_data",
        ),
        (
            lambda laptop, accessory: accessory["requirements"].update(host_usb_c_video=True),
            "insufficient_data",
        ),
        (lambda laptop, accessory: laptop["ports"].update(usb_c_pd_input_min_w=65), "insufficient_data"),
        (lambda laptop, accessory: laptop["ports"].update(usb_c_pd_input_min_w=None), "insufficient_data"),
        (lambda laptop, accessory: laptop["ports"].update(usb_c_pd_input_max_w=None), "insufficient_data"),
        (
            lambda laptop, accessory: accessory["outputs"].update(charging_output_watts=66),
            "insufficient_data",
        ),
        (
            lambda laptop, accessory: accessory["outputs"].update(charging_output_watts=45),
            "insufficient_data",
        ),
        (lambda laptop, accessory: accessory["outputs"].update(charging_output_watts=44), "incompatible"),
    ],
)
def test_additional_display_connection_and_charging_scenarios(mutation, expected: str) -> None:
    laptop, accessory = records()
    mutation(laptop, accessory)
    result = check(laptop, accessory, external_displays=2, laptop_charging=True)
    assert result["verdict"] == expected


def test_failure_takes_precedence_over_unknown_and_limit() -> None:
    laptop, accessory = records()
    laptop["ports"].update(usb_c_video_supported=False, maximum_external_displays=None)
    accessory["outputs"].update(charging_output_watts=50)
    result = check(laptop, accessory, laptop_charging=True)
    assert result["verdict"] == "incompatible"
    assert result["limits"]


def test_no_external_display_does_not_require_display_mode_facts() -> None:
    laptop, accessory = records()
    laptop["ports"].update(usb_c_video_supported=None, usb_c_max_resolution=None, usb_c_max_refresh_hz=None)
    accessory["outputs"].update(display_count=None, hdmi_max_resolution=None, hdmi_max_refresh_hz=None)
    result = check(laptop, accessory, external_displays=0)
    assert result["verdict"] == "compatible"


def test_explicit_simultaneous_configuration_is_supported_when_both_sources_document_it() -> None:
    laptop, accessory = records()
    modes = [
        {"resolution": "3840x2160", "refresh_rate_hz": 60},
        {"resolution": "1920x1080", "refresh_rate_hz": 60},
    ]
    laptop["ports"]["display_configurations"] = [{"displays": modes, "topology": "extended"}]
    accessory["outputs"]["display_configurations"] = [{"displays": modes, "topology": "extended"}]
    result = check(
        laptop,
        accessory,
        displays=modes,
        display_topology="extended",
    )
    assert result["verdict"] == "compatible"
    assert {"Laptop combined display mode", "Accessory combined display mode"} <= {
        item["name"] for item in result["requirements"] if item["status"] == "passed"
    }


def test_individual_maxima_do_not_establish_combined_bandwidth_or_topology() -> None:
    laptop, accessory = records()
    modes = [
        {"resolution": "3840x2160", "refresh_rate_hz": 60},
        {"resolution": "1920x1080", "refresh_rate_hz": 60},
    ]
    laptop["ports"]["display_configurations"] = [{"displays": modes}]
    accessory["outputs"]["display_configurations"] = [{"displays": modes}]
    result = check(laptop, accessory, displays=modes, display_topology="daisy-chain")
    assert result["verdict"] == "insufficient_data"
    assert any("aggregate bandwidth or lane allocation" in item["detail"] for item in result["requirements"])


def test_documented_laptop_display_count_limit_still_reports_a_specific_failure() -> None:
    laptop, accessory = records()
    laptop["ports"]["maximum_external_displays"] = 1
    modes = [
        {"resolution": "1920x1080", "refresh_rate_hz": 60},
        {"resolution": "1920x1080", "refresh_rate_hz": 60},
    ]
    result = check(laptop, accessory, displays=modes)
    assert result["verdict"] == "incompatible"
    assert any(
        item["name"] == "Display count" and item["status"] == "failed" for item in result["requirements"]
    )


def test_configuration_match_does_not_abort_when_first_config_lacks_topology() -> None:
    from app.rules import _configuration_match

    modes = [
        {"resolution": "1920x1080", "refresh_rate_hz": 60},
        {"resolution": "1920x1080", "refresh_rate_hz": 60},
    ]
    configurations = [
        {"displays": modes, "topology": None},
        {"displays": modes, "topology": "extended"},
    ]
    assert _configuration_match(configurations, modes, "extended") is True


def test_multi_display_modes_without_host_dp_reports_unmodeled_alternate_video_path() -> None:
    laptop, accessory = records()
    accessory["requirements"]["host_usb_c_video"] = False
    modes = [
        {"resolution": "1920x1080", "refresh_rate_hz": 60},
        {"resolution": "1920x1080", "refresh_rate_hz": 60},
    ]
    accessory["outputs"]["display_configurations"] = [{"displays": modes, "topology": "extended"}]
    result = check(laptop, accessory, displays=modes, display_topology="extended")
    assert result["verdict"] == "insufficient_data"
    req_details = {item["name"]: item["detail"] for item in result["requirements"]}
    assert "The accessory does not require DisplayPort Alt Mode" in req_details.get(
        "Laptop combined display mode", ""
    )
    assert not any(
        "The request specifies a display count but not each simultaneous mode" in item["detail"]
        for item in result["requirements"]
    )
