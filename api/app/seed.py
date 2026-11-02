from datetime import date

from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import AccessoryModel, LaptopModel, SourceEvidence

CHECKED_ON = date(2026, 11, 2)

SEED_IDENTITY_FIELDS = {"id", "brand", "name", "category", "region_variant", "review_status"}


def validate_seed_record(record: dict) -> None:
    """Fail closed if a verified seed record lacks evidence for a populated field."""
    if record.get("review_status") not in {"verified", "draft", "needs_review"}:
        raise ValueError(f"Seed record {record.get('id')} has an invalid review status.")
    required_metadata = ("source_title", "source_url", "excerpt")
    if any(not record.get(field) for field in required_metadata):
        raise ValueError(f"Seed record {record.get('id')} is missing source metadata.")

    evidence_keys = record.get("evidence", [])
    if len(evidence_keys) != len(set(evidence_keys)):
        raise ValueError(f"Seed record {record.get('id')} has duplicate evidence capabilities.")
    excerpts = record.get("evidence_excerpts", {})
    for key in evidence_keys:
        if key in excerpts and not excerpts[key].strip():
            raise ValueError(f"Seed record {record.get('id')} has an empty capability excerpt for {key}.")

    missing = sorted(
        key
        for key, value in record.items()
        if value is not None
        and key not in SEED_IDENTITY_FIELDS
        and key not in {"source_title", "source_url", "excerpt", "evidence", "evidence_excerpts"}
        and key not in evidence_keys
    )
    if missing:
        raise ValueError(
            f"Seed record {record.get('id')} has populated fields without evidence: {', '.join(missing)}."
        )


LAPTOPS = [
    {
        "id": "lenovo-ideapad-slim-3-14irh10r",
        "brand": "Lenovo",
        "name": "Lenovo IdeaPad Slim 3 14IRH10R",
        "model_code": "14IRH10R",
        "region_variant": None,
        "operating_system": "Windows 11",
        "usb_c_port_count": 1,
        "usb_c_data_rate_gbps": 5,
        "usb_c_video_supported": True,
        "usb_c_dp_version": "1.2",
        "usb_c_pd_input_min_w": 45,
        "usb_c_pd_input_max_w": 65,
        "hdmi_version": "1.4",
        "hdmi_max_resolution": "4K",
        "hdmi_max_refresh_hz": 30,
        "maximum_external_displays": 2,
        "usb_c_max_resolution": "4K",
        "usb_c_max_refresh_hz": 60,
        "review_status": "verified",
        "source_title": "Lenovo PSREF: IdeaPad Slim 3 14IRH10R",
        "source_url": "https://psref.lenovo.com/Product/IdeaPad/IdeaPad_Slim_3_14IRH10R",
        "excerpt": "1x USB-C (USB 5Gbps / USB 3.2 Gen 1), with USB PD 45-65W and DisplayPort 1.2.",
        "evidence_excerpts": {
            "model_code": "Lenovo product identifier: IdeaPad Slim 3 14IRH10R.",
            "hdmi_version": "1x HDMI 1.4.",
            "hdmi_max_resolution": "HDMI supports up to 4K.",
            "hdmi_max_refresh_hz": "HDMI supports up to 30Hz at 4K.",
            "maximum_external_displays": "3 displays: 1 built-in plus 2 external.",
            "usb_c_max_resolution": "USB-C supports up to 4K.",
            "usb_c_max_refresh_hz": "USB-C supports up to 60Hz at 4K.",
            "operating_system": "Windows 11 Pro is an available operating system.",
        },
        "evidence": [
            "model_code",
            "usb_c_port_count",
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
            "operating_system",
        ],
    },
    {
        "id": "lenovo-ideapad-slim-3-15irh10r",
        "brand": "Lenovo",
        "name": "Lenovo IdeaPad Slim 3 15IRH10R",
        "model_code": "15IRH10R",
        "region_variant": None,
        "operating_system": "Windows 11",
        "usb_c_port_count": 1,
        "usb_c_data_rate_gbps": 5,
        "usb_c_video_supported": True,
        "usb_c_dp_version": "1.2",
        "usb_c_pd_input_min_w": 45,
        "usb_c_pd_input_max_w": 65,
        "hdmi_version": "1.4",
        "hdmi_max_resolution": "4K",
        "hdmi_max_refresh_hz": 30,
        "maximum_external_displays": 2,
        "usb_c_max_resolution": "4K",
        "usb_c_max_refresh_hz": 60,
        "review_status": "verified",
        "source_title": "Lenovo PSREF: IdeaPad Slim 3 15IRH10R",
        "source_url": "https://psref.lenovo.com/Product/IdeaPad_Slim_3_15IRH10R",
        "excerpt": "1x USB-C (USB 5Gbps / USB 3.2 Gen 1), with USB PD 45-65W and DisplayPort 1.2.",
        "evidence_excerpts": {
            "model_code": "Lenovo product identifier: IdeaPad Slim 3 15IRH10R.",
            "hdmi_version": "1x HDMI 1.4.",
            "hdmi_max_resolution": "HDMI supports up to 4K.",
            "hdmi_max_refresh_hz": "HDMI supports up to 30Hz at 4K.",
            "maximum_external_displays": "3 displays: 1 built-in plus 2 external.",
            "usb_c_max_resolution": "USB-C supports up to 4K.",
            "usb_c_max_refresh_hz": "USB-C supports up to 60Hz at 4K.",
            "operating_system": "Windows 11 Pro is an available operating system.",
        },
        "evidence": [
            "model_code",
            "usb_c_port_count",
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
            "operating_system",
        ],
    },
    {
        "id": "lenovo-ideapad-slim-3-14itn9",
        "brand": "Lenovo",
        "name": "Lenovo IdeaPad Slim 3 14ITN9",
        "model_code": "14ITN9",
        "region_variant": None,
        "operating_system": "Windows 11",
        "usb_c_port_count": 1,
        "usb_c_data_rate_gbps": 5,
        "usb_c_video_supported": True,
        "usb_c_dp_version": "1.2",
        "usb_c_pd_input_min_w": 45,
        "usb_c_pd_input_max_w": 65,
        "hdmi_version": "1.4",
        "hdmi_max_resolution": "4K",
        "hdmi_max_refresh_hz": 30,
        "maximum_external_displays": 2,
        "usb_c_max_resolution": "4K",
        "usb_c_max_refresh_hz": 60,
        "review_status": "verified",
        "source_title": "Lenovo PSREF: IdeaPad Slim 3 14ITN9",
        "source_url": "https://psref.lenovo.com/Product/IdeaPad/IdeaPad_Slim_3_14ITN9",
        "excerpt": "1x USB-C (USB 5Gbps / USB 3.2 Gen 1), with USB PD 45-65W and DisplayPort 1.2.",
        "evidence_excerpts": {
            "model_code": "Lenovo product identifier: IdeaPad Slim 3 14ITN9.",
            "hdmi_version": "1x HDMI 1.4.",
            "hdmi_max_resolution": "HDMI supports up to 4K.",
            "hdmi_max_refresh_hz": "HDMI supports up to 30Hz at 4K.",
            "maximum_external_displays": "3 displays: 1 built-in plus 2 external.",
            "usb_c_max_resolution": "USB-C supports up to 4K.",
            "usb_c_max_refresh_hz": "USB-C supports up to 60Hz at 4K.",
            "operating_system": "Windows 11 Pro is an available operating system.",
        },
        "evidence": [
            "model_code",
            "usb_c_port_count",
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
            "operating_system",
        ],
    },
    {
        "id": "lenovo-ideapad-slim-5-15arp10",
        "brand": "Lenovo",
        "name": "Lenovo IdeaPad Slim 5 15ARP10",
        "model_code": "15ARP10",
        "region_variant": None,
        "operating_system": "Windows 11",
        "usb_c_port_count": 2,
        "usb_c_data_rate_gbps": 10,
        "usb_c_video_supported": True,
        "usb_c_dp_version": "1.4",
        "usb_c_pd_input_min_w": 45,
        "usb_c_pd_input_max_w": 65,
        "hdmi_version": "2.1",
        "hdmi_max_resolution": "4K",
        "hdmi_max_refresh_hz": 60,
        "maximum_external_displays": 3,
        "usb_c_max_resolution": "4K",
        "usb_c_max_refresh_hz": 60,
        "review_status": "verified",
        "source_title": "Lenovo PSREF: IdeaPad Slim 5 15ARP10",
        "source_url": "https://psref.lenovo.com/Product/IdeaPad_Slim_5_15ARP10",
        "excerpt": "2x USB-C (USB 10Gbps), with USB PD 45-65W and DisplayPort 1.4; HDMI 2.1 up to 4K/60Hz.",
        "evidence_excerpts": {
            "model_code": "Lenovo product identifier: IdeaPad Slim 5 15ARP10.",
            "maximum_external_displays": "4 displays: 1 built-in plus 3 external.",
            "usb_c_max_resolution": "USB-C supports up to 4K.",
            "usb_c_max_refresh_hz": "USB-C supports up to 60Hz at 4K.",
            "operating_system": "Windows 11 Pro is an available operating system.",
        },
        "evidence": [
            "model_code",
            "usb_c_port_count",
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
            "operating_system",
        ],
    },
    {
        "id": "lenovo-ideapad-slim-3-15iru8",
        "brand": "Lenovo",
        "name": "Lenovo IdeaPad Slim 3 15IRU8",
        "model_code": "15IRU8",
        "region_variant": None,
        "operating_system": "Windows 11",
        "usb_c_port_count": 1,
        "usb_c_data_rate_gbps": 5,
        "usb_c_video_supported": True,
        "usb_c_dp_version": "1.2",
        "usb_c_pd_input_min_w": 45,
        "usb_c_pd_input_max_w": 65,
        "hdmi_version": "1.4",
        "hdmi_max_resolution": "4K",
        "hdmi_max_refresh_hz": 30,
        "maximum_external_displays": 2,
        "usb_c_max_resolution": "4K",
        "usb_c_max_refresh_hz": 60,
        "review_status": "verified",
        "source_title": "Lenovo PSREF: IdeaPad Slim 3 15IRU8",
        "source_url": "https://support.lenovo.com/in/en/manuals/um927968-product-specifications-reference-psref-ideapad-slim-3-15iru8",
        "excerpt": "USB-C 3.2 Gen 1 supports data transfer, USB PD 45-65W, and DisplayPort 1.2.",
        "evidence_excerpts": {
            "model_code": "Lenovo product identifier: IdeaPad Slim 3 15IRU8.",
            "hdmi_version": "1x HDMI 1.4b.",
            "hdmi_max_resolution": "HDMI supports up to 4K.",
            "hdmi_max_refresh_hz": "HDMI supports up to 30Hz at 4K.",
            "maximum_external_displays": "3 displays: 1 built-in plus 2 external.",
            "usb_c_max_resolution": "USB-C supports up to 4K.",
            "usb_c_max_refresh_hz": "USB-C supports up to 60Hz at 4K.",
            "operating_system": "Windows 11 Pro is an available operating system.",
        },
        "evidence": [
            "model_code",
            "usb_c_port_count",
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
            "operating_system",
        ],
    },
]


def sourced_laptop(model_code: str, name: str, product_url: str, port_excerpt: str, dp_version: str) -> dict:
    """Build a minimally populated laptop record from its exact Lenovo PSREF configuration."""
    record_id = f"lenovo-{model_code.lower()}"
    return {
        "id": record_id,
        "brand": "Lenovo",
        "name": name,
        "model_code": model_code,
        "region_variant": None,
        "operating_system": None,
        "usb_c_port_count": 2,
        "usb_c_data_rate_gbps": None,
        "usb_c_video_supported": True,
        "usb_c_dp_version": dp_version,
        "usb_c_pd_input_min_w": None,
        "usb_c_pd_input_max_w": None,
        "hdmi_version": None,
        "hdmi_max_resolution": None,
        "hdmi_max_refresh_hz": None,
        "maximum_external_displays": None,
        "usb_c_max_resolution": None,
        "usb_c_max_refresh_hz": None,
        "review_status": "verified",
        "source_title": f"Lenovo PSREF: {name} ({model_code})",
        "source_url": product_url,
        "excerpt": port_excerpt,
        "evidence_excerpts": {
            "model_code": f"Lenovo PSREF identifies this configuration as model {model_code}.",
            "usb_c_port_count": port_excerpt,
            "usb_c_video_supported": port_excerpt,
            "usb_c_dp_version": (
                f"Minimum specified DisplayPort version across the model's USB-C ports: DP {dp_version}."
            ),
        },
        "evidence": ["model_code", "usb_c_port_count", "usb_c_video_supported", "usb_c_dp_version"],
    }


LAPTOPS.extend(
    [
        sourced_laptop(
            "21MR004UIV",
            "ThinkBook 14 G7 IML",
            "https://psref.lenovo.com/Detail/ThinkBook/ThinkBook_14_G7_IML?M=21MR004UIV",
            "USB-C 10Gbps with DP 1.4; Thunderbolt 4/USB4 40Gbps with DP 2.1.",
            "1.4",
        ),
        sourced_laptop(
            "21MS00AGAD",
            "ThinkBook 16 G7 IML",
            "https://psref.lenovo.com/Detail/ThinkBook_16_G7_IML?M=21MS00AGAD",
            "USB-C 10Gbps with DP 1.4; Thunderbolt 4/USB4 40Gbps with DP 2.1.",
            "1.4",
        ),
        sourced_laptop(
            "21M7006CMY",
            "ThinkPad E14 Gen 6 (Intel)",
            "https://psref.lenovo.com/Detail/ThinkPad_E14_Gen_6_Intel?M=21M7006CMY",
            "1x USB-C 20Gbps with DisplayPort 1.4; 1x Thunderbolt 4/USB4 40Gbps with DisplayPort 2.1.",
            "1.4",
        ),
        sourced_laptop(
            "21M300B2GY",
            "ThinkPad E14 Gen 6 (AMD)",
            "https://psref.lenovo.com/Detail/ThinkPad_E14_Gen_6_AMD?M=21M300B2GY",
            "Two USB-C ports with Power Delivery and DisplayPort 1.4.",
            "1.4",
        ),
        sourced_laptop(
            "83DA009CAX",
            "IdeaPad Slim 5 14IMH9",
            "https://psref.lenovo.com/Detail/IdeaPad_Slim_5_14IMH9?M=83DA009CAX",
            "2x USB-C ports with USB PD 3.0 and DisplayPort 1.4.",
            "1.4",
        ),
        sourced_laptop(
            "83V6002FTR",
            "IdeaPad Slim 5 14IMH10",
            "https://psref.lenovo.com/Detail/IdeaPad_Slim_5_14IMH10?M=83V6002FTR",
            "2x USB-C 10Gbps with USB PD 65-100W and DisplayPort 1.4.",
            "1.4",
        ),
        sourced_laptop(
            "83HV004FKR",
            "IdeaPad Slim 5 14AHP10",
            "https://psref.lenovo.com/Detail/ideapad_slim_5_14ahp10?M=83HV004FKR",
            "2x USB-C 10Gbps with USB PD 65-100W and DisplayPort 1.4.",
            "1.4",
        ),
        sourced_laptop(
            "21T1001LVQ",
            "ThinkPad E14 Gen 7 (AMD)",
            "https://psref.lenovo.com/Detail/ThinkPad_E14_Gen_7_AMD?M=21T1001LVQ",
            "1x USB-C 5Gbps and 1x USB4 40Gbps, both with USB PD and DisplayPort 1.4 or 1.4a.",
            "1.4",
        ),
        sourced_laptop(
            "83S50008IN",
            "IdeaPad Slim 5 14IPH11",
            "https://psref.lenovo.com/Detail/IdeaPad_Slim_5_14IPH11?M=83S50008IN",
            "2x USB-C 10Gbps with USB PD 65-100W and DisplayPort 1.2.",
            "1.2",
        ),
        sourced_laptop(
            "83S5008YIN",
            "IdeaPad Slim 5 14IPH11",
            "https://psref.lenovo.com/Detail/IdeaPad_Slim_5_14IPH11?M=83S5008YIN",
            "2x USB-C ports with USB PD 65-100W and DisplayPort 1.2.",
            "1.2",
        ),
    ]
)

ACCESSORIES = [
    {
        "id": "anker-364-usb-c-hub",
        "brand": "Anker",
        "name": "Anker 364 USB-C Hub (10-in-1, Dual 4K HDMI)",
        "model_code": None,
        "category": "usb_c_hub",
        "host_connection": "USB-C",
        "requires_usb_c_dp_alt_mode": None,
        "hdmi_port_count": 2,
        "hdmi_max_resolution": "4K",
        "hdmi_max_refresh_hz": 60,
        "pd_input_max_w": 100,
        "pd_pass_through_max_w": 85,
        "usb_c_output_max_w": None,
        "usb_a_port_count": 3,
        "ethernet_max_gbps": 1,
        "review_status": "verified",
        "source_title": "Anker 364 USB-C Hub product specifications",
        "source_url": "https://service.anker.com/product-description/a085g000004zuplAAA",
        "excerpt": "Anker lists the hub's HDMI, Power Delivery, USB-A, and Ethernet port specifications.",
        "evidence_excerpts": {
            "host_connection": "Anker 364 USB-C Hub product title.",
            "hdmi_port_count": "2 x HDMI outputs.",
            "hdmi_max_resolution": "HDMI outputs up to 4K (3840 x 2160).",
            "hdmi_max_refresh_hz": "HDMI outputs up to 60Hz.",
            "pd_input_max_w": "PD input up to 100W output.",
            "pd_pass_through_max_w": "85W output maximum PD pass-through.",
            "usb_a_port_count": "3 x USB-A data ports.",
            "ethernet_max_gbps": "1 x Ethernet port, 1Gbps.",
        },
        "evidence": [
            "host_connection",
            "hdmi_port_count",
            "hdmi_max_resolution",
            "hdmi_max_refresh_hz",
            "pd_input_max_w",
            "pd_pass_through_max_w",
            "usb_a_port_count",
            "ethernet_max_gbps",
        ],
    },
    {
        "id": "anker-555-usb-c-hub",
        "brand": "Anker",
        "name": "Anker 555 USB-C Hub (8-in-1)",
        "model_code": "A8383",
        "category": "usb_c_hub",
        "host_connection": "USB-C",
        "requires_usb_c_dp_alt_mode": True,
        "hdmi_port_count": 1,
        "hdmi_max_resolution": "4K",
        "hdmi_max_refresh_hz": 60,
        "pd_input_max_w": 85,
        "pd_pass_through_max_w": None,
        "usb_c_output_max_w": None,
        "usb_a_port_count": 2,
        "ethernet_max_gbps": 1,
        "review_status": "verified",
        "source_title": "Anker 555 USB-C Hub product specifications",
        "source_url": "https://service.anker.com/product-description/a085g000004x2CVAAY/anker-555-usbc-hub-8in1",
        "excerpt": "Anker product specifications for this hub.",
        "evidence_excerpts": {
            "model_code": "Anker 555 USB-C Hub user manual model A8383.",
            "host_connection": "Compatible laptops need a USB-C host port.",
            "requires_usb_c_dp_alt_mode": "Host USB-C must support Power Delivery and DisplayPort Alt Mode.",
            "hdmi_port_count": "1 x HDMI port.",
            "hdmi_max_resolution": "HDMI output supports up to 4K.",
            "hdmi_max_refresh_hz": "HDMI output supports up to 60Hz.",
            "pd_input_max_w": "1 x USB-C PD-IN port, 85W max.",
            "usb_a_port_count": "2 x USB-A data ports.",
            "ethernet_max_gbps": "1 x Ethernet port, 1Gbps.",
        },
        "evidence": [
            "model_code",
            "host_connection",
            "requires_usb_c_dp_alt_mode",
            "hdmi_port_count",
            "hdmi_max_resolution",
            "hdmi_max_refresh_hz",
            "pd_input_max_w",
            "usb_a_port_count",
            "ethernet_max_gbps",
        ],
    },
    {
        "id": "anker-543-usb-c-hub",
        "brand": "Anker",
        "name": "Anker 543 USB-C Hub (6-in-1, Slim)",
        "model_code": "A8365",
        "category": "usb_c_hub",
        "host_connection": "USB-C",
        "requires_usb_c_dp_alt_mode": True,
        "hdmi_port_count": 1,
        "hdmi_max_resolution": "4K",
        "hdmi_max_refresh_hz": 30,
        "pd_input_max_w": 53,
        "pd_pass_through_max_w": None,
        "usb_c_output_max_w": None,
        "usb_a_port_count": 2,
        "ethernet_max_gbps": 1,
        "review_status": "verified",
        "source_title": "Anker 543 USB-C Hub product specifications",
        "source_url": "https://service.anker.com/product-description/a085g000004x2CeAAI/anker-543-usbc-hub-6in1-slim",
        "excerpt": "Anker product specifications for this hub.",
        "evidence_excerpts": {
            "model_code": "Anker 543 USB-C Hub user guide model A8365.",
            "host_connection": "Compatible laptops need a USB-C host port.",
            "requires_usb_c_dp_alt_mode": "Host USB-C must support Power Delivery and DisplayPort Alt Mode.",
            "hdmi_port_count": "1 x HDMI port.",
            "hdmi_max_resolution": "HDMI output supports 4K.",
            "hdmi_max_refresh_hz": "HDMI output supports 30Hz.",
            "pd_input_max_w": "1 x USB-C PD-IN port, 53W max.",
            "usb_a_port_count": "2 x USB-A data ports.",
            "ethernet_max_gbps": "1 x Ethernet port, 1Gbps.",
        },
        "evidence": [
            "model_code",
            "host_connection",
            "requires_usb_c_dp_alt_mode",
            "hdmi_port_count",
            "hdmi_max_resolution",
            "hdmi_max_refresh_hz",
            "pd_input_max_w",
            "usb_a_port_count",
            "ethernet_max_gbps",
        ],
    },
    {
        "id": "anker-655-usb-c-hub",
        "brand": "Anker",
        "name": "Anker 655 USB-C Hub (8-in-1)",
        "model_code": "A8382",
        "category": "usb_c_hub",
        "host_connection": "USB-C",
        "requires_usb_c_dp_alt_mode": True,
        "hdmi_port_count": 1,
        "hdmi_max_resolution": "4K",
        "hdmi_max_refresh_hz": 60,
        "pd_input_max_w": 85,
        "pd_pass_through_max_w": None,
        "usb_c_output_max_w": None,
        "usb_a_port_count": 2,
        "ethernet_max_gbps": 1,
        "review_status": "verified",
        "source_title": "Anker 655 USB-C Hub product specifications",
        "source_url": "https://service.anker.com/product-description/a085g000004x2CXAAY/anker-655-usbc-hub-8in1",
        "excerpt": "Anker product specifications for this hub.",
        "evidence_excerpts": {
            "model_code": "Anker 655 USB-C Hub user manual model A8382.",
            "host_connection": "Compatible laptops need a USB-C host port.",
            "requires_usb_c_dp_alt_mode": "Host USB-C must support Power Delivery and DisplayPort Alt Mode.",
            "hdmi_port_count": "1 x HDMI port.",
            "hdmi_max_resolution": "HDMI output supports up to 4K.",
            "hdmi_max_refresh_hz": "HDMI output supports up to 60Hz.",
            "pd_input_max_w": "1 x USB-C PD-IN port, 85W max.",
            "usb_a_port_count": "2 x USB-A data ports.",
            "ethernet_max_gbps": "1 x Ethernet port, 1Gbps.",
        },
        "evidence": [
            "model_code",
            "host_connection",
            "requires_usb_c_dp_alt_mode",
            "hdmi_port_count",
            "hdmi_max_resolution",
            "hdmi_max_refresh_hz",
            "pd_input_max_w",
            "usb_a_port_count",
            "ethernet_max_gbps",
        ],
    },
    {
        "id": "anker-715-usb-c-charger-65w",
        "brand": "Anker",
        "name": "Anker 715 Charger (Nano II 65W)",
        "model_code": "A2663",
        "category": "usb_c_charger",
        "host_connection": "USB-C",
        "requires_usb_c_dp_alt_mode": None,
        "hdmi_port_count": None,
        "hdmi_max_resolution": None,
        "hdmi_max_refresh_hz": None,
        "pd_input_max_w": None,
        "pd_pass_through_max_w": None,
        "usb_c_output_max_w": 65,
        "usb_a_port_count": 0,
        "ethernet_max_gbps": None,
        "review_status": "verified",
        "source_title": "Anker 715 Charger product specifications",
        "source_url": "https://www.anker.com/products/a2663",
        "excerpt": "Anker lists one USB-C output port with a maximum 65W output and no USB-A output port.",
        "evidence_excerpts": {
            "model_code": "Anker 715 Charger model number A2663.",
            "host_connection": "The charger has one USB-C output port.",
            "usb_c_output_max_w": "USB-C output: 20V at 3.25A (65W max).",
            "usb_a_port_count": "Total USB-A ports: 0.",
        },
        "evidence": ["model_code", "host_connection", "usb_c_output_max_w", "usb_a_port_count"],
    },
]


def sourced_accessory(
    *,
    record_id: str,
    brand: str,
    name: str,
    model_code: str,
    category: str,
    source_title: str,
    source_url: str,
    specifications: dict,
    excerpts: dict,
) -> dict:
    values = {
        "id": record_id,
        "brand": brand,
        "name": name,
        "model_code": model_code,
        "category": category,
        "host_connection": "USB-C",
        "requires_usb_c_dp_alt_mode": None,
        "hdmi_port_count": None,
        "hdmi_max_resolution": None,
        "hdmi_max_refresh_hz": None,
        "pd_input_max_w": None,
        "pd_pass_through_max_w": None,
        "usb_c_output_max_w": None,
        "usb_a_port_count": None,
        "ethernet_max_gbps": None,
        "review_status": "verified",
    }
    values.update(specifications)
    evidence = [
        key
        for key, value in values.items()
        if value is not None and key not in {"id", "brand", "name", "review_status"}
    ]
    return {
        **values,
        "source_title": source_title,
        "source_url": source_url,
        "excerpt": f"Official {brand} product specifications for {model_code}.",
        "evidence_excerpts": excerpts,
        "evidence": evidence,
    }


ACCESSORIES.extend(
    [
        sourced_accessory(
            record_id="anker-nano-hub-7in1-a83d2",
            brand="Anker",
            name="Anker Nano USB-C Hub 7-in-1",
            model_code="A83D2",
            category="usb_c_hub",
            source_title="Anker Nano USB-C Hub 7-in-1 User Guide",
            source_url="https://support.anker.com/s/article/Anker-Nano-USB-C-Hub-7-in-1-4K-HDMI-User-Guide-A83D2",
            specifications={
                "requires_usb_c_dp_alt_mode": True,
                "hdmi_port_count": 1,
                "hdmi_max_resolution": "4K",
                "hdmi_max_refresh_hz": 60,
                "pd_input_max_w": 100,
                "pd_pass_through_max_w": 85,
            },
            excerpts={
                "model_code": "Anker identifies this hub as model A83D2.",
                "category": "Anker describes the product as a USB-C hub.",
                "host_connection": "The hub connects to the host through USB-C.",
                "requires_usb_c_dp_alt_mode": "Host USB-C needs DP Alt Mode and Power Delivery.",
                "hdmi_port_count": "1 HDMI port.",
                "hdmi_max_resolution": "HDMI supports up to 4K resolution.",
                "hdmi_max_refresh_hz": "HDMI supports up to 60Hz.",
                "pd_input_max_w": "PD input supports up to 100W.",
                "pd_pass_through_max_w": "Hub pass-through output is up to 85W after power allocation.",
            },
        ),
        sourced_accessory(
            record_id="anker-nano-hub-6in1-a83c3",
            brand="Anker",
            name="Anker Nano USB-C Hub 6-in-1",
            model_code="A83C3",
            category="usb_c_hub",
            source_title="Anker Nano USB-C Hub 6-in-1",
            source_url="https://www.anker.com/uk/products/a83c3-anker-nano-usb-c-hub-6-in-1",
            specifications={
                "requires_usb_c_dp_alt_mode": True,
                "hdmi_port_count": 1,
                "hdmi_max_resolution": "4K",
                "hdmi_max_refresh_hz": 60,
                "pd_input_max_w": 100,
                "pd_pass_through_max_w": 85,
            },
            excerpts={
                "model_code": "Anker product identifies the hub as A83C3.",
                "category": "Anker describes the product as a USB-C hub.",
                "host_connection": "The hub connects to the host through USB-C.",
                "requires_usb_c_dp_alt_mode": "Laptop USB-C needs DP Alt Mode and Power Delivery.",
                "hdmi_port_count": "1 HDMI port.",
                "hdmi_max_resolution": "HDMI supports up to 4K resolution.",
                "hdmi_max_refresh_hz": "HDMI supports up to 60Hz.",
                "pd_input_max_w": "PD-IN supports up to 100W.",
                "pd_pass_through_max_w": "Hub upstream output is up to 85W.",
            },
        ),
        sourced_accessory(
            record_id="ugreen-hub-6in1-60384",
            brand="UGREEN",
            name="UGREEN 6-in-1 USB-C Hub",
            model_code="60384",
            category="usb_c_hub",
            source_title="UGREEN 6-in-1 USB-C Hub product specifications",
            source_url="https://uk.ugreen.com/products/ugreen-6-in-1-usb-c-hub-4k-60hz-hdmi-100w-pd",
            specifications={
                "requires_usb_c_dp_alt_mode": True,
                "hdmi_port_count": 1,
                "hdmi_max_resolution": "4K",
                "hdmi_max_refresh_hz": 60,
                "pd_input_max_w": 100,
                "pd_pass_through_max_w": 85,
            },
            excerpts={
                "model_code": "UGREEN identifies the product by SKU 60384.",
                "category": "UGREEN describes the product as a USB-C hub.",
                "host_connection": "The hub connects to the host through USB-C.",
                "requires_usb_c_dp_alt_mode": "Host requires DP Alt Mode; DP 1.4 is specified for 4K/60Hz.",
                "hdmi_port_count": "1 HDMI port.",
                "hdmi_max_resolution": "HDMI supports 4K.",
                "hdmi_max_refresh_hz": "HDMI supports up to 60Hz with a DP 1.4 host.",
                "pd_input_max_w": "USB-C PD input supports up to 100W.",
                "pd_pass_through_max_w": "Up to 85W is delivered to the connected laptop.",
            },
        ),
        sourced_accessory(
            record_id="ugreen-hub-7in1-60515",
            brand="UGREEN",
            name="UGREEN 7-in-1 Multiport Adapter",
            model_code="60515",
            category="usb_c_hub",
            source_title="UGREEN 7-in-1 Multiport Adapter product specifications",
            source_url="https://us.ugreen.com/products/7-in-1-multiport-adapter-with-4k-60hz",
            specifications={
                "requires_usb_c_dp_alt_mode": True,
                "hdmi_port_count": 1,
                "hdmi_max_resolution": "4K",
                "hdmi_max_refresh_hz": 60,
                "pd_input_max_w": 100,
                "pd_pass_through_max_w": 95,
            },
            excerpts={
                "model_code": "UGREEN identifies the product as SKU 60515.",
                "category": "UGREEN describes the product as a multiport USB-C adapter.",
                "host_connection": "The adapter connects to the host through USB-C.",
                "requires_usb_c_dp_alt_mode": "Host USB-C needs video; DP 1.4 is required for 4K/60Hz.",
                "hdmi_port_count": "1 HDMI port.",
                "hdmi_max_resolution": "HDMI supports up to 4K.",
                "hdmi_max_refresh_hz": "HDMI supports up to 60Hz with DP 1.4.",
                "pd_input_max_w": "USB-C PD input supports up to 100W.",
                "pd_pass_through_max_w": "Up to 95W pass-through output.",
            },
        ),
        sourced_accessory(
            record_id="ugreen-revodok-pro-106-45363",
            brand="UGREEN",
            name="UGREEN Revodok Pro 106 6-in-1 Hub",
            model_code="45363",
            category="usb_c_hub",
            source_title="UGREEN Revodok Pro 106 product specifications",
            source_url="https://us.ugreen.com/products/6-in-1-usb-c-hub-4k",
            specifications={
                "requires_usb_c_dp_alt_mode": True,
                "hdmi_port_count": 1,
                "hdmi_max_resolution": "4K",
                "hdmi_max_refresh_hz": 60,
                "pd_input_max_w": 100,
                "pd_pass_through_max_w": 85,
            },
            excerpts={
                "model_code": "UGREEN identifies the product by SKU 45363.",
                "category": "UGREEN describes the product as a USB-C hub.",
                "host_connection": "The hub connects to the host through USB-C.",
                "requires_usb_c_dp_alt_mode": "Host requires DP Alt Mode; DP 1.4 is specified for 4K/60Hz.",
                "hdmi_port_count": "1 HDMI port.",
                "hdmi_max_resolution": "HDMI supports 4K.",
                "hdmi_max_refresh_hz": "HDMI supports up to 60Hz.",
                "pd_input_max_w": "PD input supports up to 100W.",
                "pd_pass_through_max_w": "Laptop charging output is up to 85W.",
            },
        ),
        sourced_accessory(
            record_id="belkin-5port-hub-avc022",
            brand="Belkin",
            name="Belkin 5-Port USB-C Hub with 4K HDMI",
            model_code="AVC022",
            category="usb_c_hub",
            source_title="Belkin AVC022 Support",
            source_url="https://www.belkin.com/uk/support-article/?articleNum=337549",
            specifications={
                "requires_usb_c_dp_alt_mode": True,
                "hdmi_port_count": 1,
                "hdmi_max_resolution": "4K",
                "hdmi_max_refresh_hz": 60,
                "pd_input_max_w": 100,
            },
            excerpts={
                "model_code": "Belkin identifies this hub as model AVC022.",
                "category": "Belkin describes the product as a USB-C hub.",
                "host_connection": "The hub connects through USB-C.",
                "requires_usb_c_dp_alt_mode": "The laptop USB-C port must support DisplayPort Alt Mode.",
                "hdmi_port_count": "1 HDMI port.",
                "hdmi_max_resolution": "HDMI supports up to 4K resolution.",
                "hdmi_max_refresh_hz": "HDMI supports up to 60Hz.",
                "pd_input_max_w": "USB-C power pass-through supports up to 100W.",
            },
        ),
        sourced_accessory(
            record_id="anker-713-charger-45w-a2664",
            brand="Anker",
            name="Anker 713 Charger (Nano II 45W)",
            model_code="A2664",
            category="usb_c_charger",
            source_title="Anker 713 Charger product specifications",
            source_url="https://service.anker.com/product-description/a085g000004x2BUAAY",
            specifications={"usb_c_output_max_w": 45},
            excerpts={
                "model_code": "Anker identifies the charger as model A2664.",
                "category": "Anker describes the product as a USB-C charger.",
                "host_connection": "The charger provides power through USB-C.",
                "usb_c_output_max_w": "Maximum USB-C output is 45W.",
            },
        ),
        sourced_accessory(
            record_id="anker-nano-charger-100w-a2679",
            brand="Anker",
            name="Anker Nano 100W USB-C Charger",
            model_code="A2679",
            category="usb_c_charger",
            source_title="Anker Nano 100W USB-C Charger",
            source_url="https://www.anker.com/products/b2679-nano-100w-usb-c-charger",
            specifications={"usb_c_output_max_w": 100},
            excerpts={
                "model_code": "Anker product identifies the charger as model A2679.",
                "category": "Anker describes the product as a USB-C charger.",
                "host_connection": "The charger provides power through USB-C.",
                "usb_c_output_max_w": "Maximum USB-C output is 100W.",
            },
        ),
        sourced_accessory(
            record_id="anker-prime-charger-100w-a2343",
            brand="Anker",
            name="Anker Prime Charger 100W",
            model_code="A2343",
            category="usb_c_charger",
            source_title="Anker Prime 100W Charger specifications",
            source_url="https://service.anker.com/product-description/a085g0000050Q24AAE",
            # The manufacturer page conflicts: 65W total output vs 100W per USB-C port.
            # Leave the compatibility-relevant charging output unknown until clarified.
            specifications={},
            excerpts={
                "model_code": "Anker identifies the charger as model A2343.",
                "category": "Anker describes the product as a multiport charger.",
                "host_connection": "The charger provides power through USB-C ports.",
            },
        ),
        sourced_accessory(
            record_id="belkin-boostcharge-65w-wca011",
            brand="Belkin",
            name="Belkin BoostCharge Compact USB-C Wall Charger 65W",
            model_code="WCA011",
            category="usb_c_charger",
            source_title="Belkin WCA011 Support",
            source_url="https://www.belkin.com/support-article/?articleNum=337468",
            specifications={"usb_c_output_max_w": 65},
            excerpts={
                "model_code": "Belkin identifies this charger as model WCA011.",
                "category": "Belkin describes the product as a USB-C wall charger.",
                "host_connection": "The charger has one USB-C output port.",
                "usb_c_output_max_w": "Maximum USB-C output is 65W.",
            },
        ),
    ]
)

# Anker also currently uses model A83C3 for a 13-in-1 docking station. Keep the
# 6-in-1 record out of public checks until the model identity is clarified.
next(row for row in ACCESSORIES if row["id"] == "anker-nano-hub-6in1-a83c3")["review_status"] = "needs_review"


def upsert_records(session: Session) -> None:
    for source in LAPTOPS:
        validate_seed_record(source)
        values = {
            key: value
            for key, value in source.items()
            if key not in {"source_title", "source_url", "excerpt", "evidence", "evidence_excerpts"}
        }
        record = session.merge(LaptopModel(**values))
        expected_evidence_ids = {f"{source['id']}:{key}" for key in source["evidence"]}
        session.query(SourceEvidence).filter(
            SourceEvidence.laptop_id == record.id,
            SourceEvidence.id.notin_(expected_evidence_ids),
        ).delete(synchronize_session=False)
        for capability_key in source["evidence"]:
            evidence = SourceEvidence(
                id=f"{source['id']}:{capability_key}",
                laptop_id=record.id,
                capability_key=capability_key,
                source_title=source["source_title"],
                source_url=source["source_url"],
                excerpt=source.get("evidence_excerpts", {}).get(capability_key, source["excerpt"]),
                checked_on=CHECKED_ON,
                review_status="verified",
            )
            session.merge(evidence)

    for source in ACCESSORIES:
        validate_seed_record(source)
        values = {
            key: value
            for key, value in source.items()
            if key not in {"source_title", "source_url", "excerpt", "evidence", "evidence_excerpts"}
        }
        record = session.merge(AccessoryModel(**values))
        expected_evidence_ids = {f"{source['id']}:{key}" for key in source["evidence"]}
        session.query(SourceEvidence).filter(
            SourceEvidence.accessory_id == record.id,
            SourceEvidence.id.notin_(expected_evidence_ids),
        ).delete(synchronize_session=False)
        for capability_key in source["evidence"]:
            evidence = SourceEvidence(
                id=f"{source['id']}:{capability_key}",
                accessory_id=record.id,
                capability_key=capability_key,
                source_title=source["source_title"],
                source_url=source["source_url"],
                excerpt=source.get("evidence_excerpts", {}).get(capability_key, source["excerpt"]),
                checked_on=CHECKED_ON,
                review_status="verified",
            )
            session.merge(evidence)


def seed() -> None:
    with SessionLocal() as session:
        upsert_records(session)
        session.commit()


if __name__ == "__main__":
    seed()
    print(f"Seeded {len(LAPTOPS)} laptops and {len(ACCESSORIES)} accessories.")
