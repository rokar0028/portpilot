import re
from typing import Any

from .schemas import CheckRequest

RULE_ENGINE_VERSION = "0.2.0"


def _mode_at_least(
    maximum_resolution: str | None,
    maximum_refresh: int | None,
    requested_resolution: str,
    requested_refresh: int,
) -> bool | None:
    """Return whether a maximum display mode covers the request, or None if unknown."""
    if maximum_resolution is None or maximum_refresh is None:
        return None

    def dimensions(value: str) -> tuple[int, int] | None:
        normalized = value.strip().lower()
        aliases = {"4k": "3840x2160", "uhd": "3840x2160", "1080p": "1920x1080", "1440p": "2560x1440"}
        match = re.fullmatch(r"(\d{3,5})x(\d{3,5})", aliases.get(normalized, normalized))
        return (int(match.group(1)), int(match.group(2))) if match else None

    requested = dimensions(requested_resolution)
    maximum = dimensions(maximum_resolution)
    if requested is None or maximum is None:
        return None
    return requested[0] <= maximum[0] and requested[1] <= maximum[1] and requested_refresh <= maximum_refresh


def evaluate(request: CheckRequest, laptop: dict[str, Any], accessory: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, str]] = []
    limits: list[str] = []
    failed = False
    unknown = False

    def add(name: str, status: str, detail: str) -> None:
        nonlocal failed, unknown
        checks.append({"status": status, "name": name, "detail": detail})
        failed |= status == "failed"
        unknown |= status == "unknown"

    setup = request.setup
    ports = laptop["ports"]
    outputs = accessory["outputs"]
    requirements = accessory["requirements"]

    # A connection is required for every setup. The initial catalogue models USB-C hosts.
    host = (accessory.get("host_connection") or "").lower()
    if "usb-c" in host or "usb c" in host:
        port_count = ports.get("usb_c_port_count")
        if port_count is None:
            add(
                "Physical connection", "unknown", "The laptop source does not establish its USB-C port count."
            )
        elif port_count < 1:
            add(
                "Physical connection", "failed", "The accessory needs USB-C, but no USB-C port is documented."
            )
        else:
            add("Physical connection", "passed", "The laptop has a documented USB-C port for this accessory.")
    elif accessory.get("host_connection") is None:
        add("Physical connection", "unknown", "The accessory source does not establish its host connection.")
    else:
        add(
            "Physical connection",
            "unknown",
            f"Host connection type {accessory['host_connection']} is not modeled yet.",
        )

    if setup.external_displays:
        dp_required = requirements.get("host_usb_c_video")
        if dp_required is True:
            video_supported = ports.get("usb_c_video_supported")
            if video_supported is True:
                add(
                    "USB-C video",
                    "passed",
                    "The laptop source confirms USB-C video and the accessory requires it.",
                )
            elif video_supported is False:
                add(
                    "USB-C video",
                    "failed",
                    "The accessory requires USB-C video, documented as unsupported on this laptop.",
                )
            else:
                add("USB-C video", "unknown", "The laptop source does not establish USB-C video support.")
        elif dp_required is False:
            add("USB-C video", "passed", "The accessory does not require USB-C video.")
        else:
            add(
                "USB-C video requirement",
                "unknown",
                "The accessory source does not establish whether USB-C video is required.",
            )

        laptop_display_limit = ports.get("maximum_external_displays")
        if laptop_display_limit is None:
            add(
                "Display count",
                "unknown",
                "The laptop source does not specify its maximum external display count.",
            )
        elif setup.external_displays > laptop_display_limit:
            add(
                "Display count",
                "failed",
                f"Requested {setup.external_displays} displays; the laptop supports "
                f"up to {laptop_display_limit}.",
            )
        else:
            add(
                "Display count",
                "passed",
                f"Requested display count is within the laptop limit of {laptop_display_limit}.",
            )

        accessory_display_limit = outputs.get("display_count")
        if accessory_display_limit is None:
            add(
                "Accessory display outputs",
                "unknown",
                "The accessory source does not establish its usable display output count.",
            )
        elif setup.external_displays > accessory_display_limit:
            add(
                "Accessory display outputs",
                "failed",
                f"Requested {setup.external_displays} displays; the accessory "
                f"provides {accessory_display_limit}.",
            )
        else:
            add(
                "Accessory display outputs",
                "passed",
                f"The accessory has enough documented outputs ({accessory_display_limit}).",
            )

        if dp_required is True:
            laptop_resolution = ports.get("usb_c_max_resolution")
            laptop_refresh = ports.get("usb_c_max_refresh_hz")
        elif dp_required is False:
            laptop_resolution = None
            laptop_refresh = None
        else:
            laptop_resolution = None
            laptop_refresh = None
        laptop_mode_ok = _mode_at_least(
            laptop_resolution, laptop_refresh, setup.resolution, setup.refresh_rate_hz
        )
        if laptop_mode_ok is None:
            add(
                "Laptop display mode",
                "unknown",
                "The laptop source does not establish the maximum mode for this display path.",
            )
        elif laptop_mode_ok:
            add(
                "Laptop display mode",
                "passed",
                f"The laptop supports at least {setup.resolution} at "
                f"{setup.refresh_rate_hz} Hz on this path.",
            )
        else:
            add(
                "Laptop display mode",
                "failed",
                f"The requested {setup.resolution} at {setup.refresh_rate_hz} Hz "
                "exceeds the laptop's documented maximum.",
            )

        if dp_required is False:
            checks[-1]["detail"] = (
                "The accessory does not require DisplayPort Alt Mode, but its alternate video path "
                "from the laptop is not modeled."
            )

        accessory_mode_ok = _mode_at_least(
            outputs.get("hdmi_max_resolution"),
            outputs.get("hdmi_max_refresh_hz"),
            setup.resolution,
            setup.refresh_rate_hz,
        )
        if accessory_mode_ok is None:
            add(
                "Accessory display mode",
                "unknown",
                "The accessory source does not establish a maximum mode for its display output.",
            )
        elif accessory_mode_ok:
            add(
                "Accessory display mode",
                "passed",
                f"The accessory supports at least {setup.resolution} at {setup.refresh_rate_hz} Hz.",
            )
        else:
            add(
                "Accessory display mode",
                "failed",
                f"The requested {setup.resolution} at {setup.refresh_rate_hz} Hz "
                "exceeds the accessory's documented maximum.",
            )

        if setup.external_displays > 1:
            add(
                "Combined display mode",
                "unknown",
                "The catalogue does not establish the maximum mode supported across all requested "
                "displays at the same time.",
            )

    if setup.laptop_charging:
        laptop_min = ports.get("usb_c_pd_input_min_w")
        laptop_max = ports.get("usb_c_pd_input_max_w")
        accessory_watts = outputs.get("charging_output_watts")
        if laptop_min is None or accessory_watts is None:
            add(
                "Charging",
                "unknown",
                "The sources do not establish the laptop's minimum charging input "
                "and accessory charging output.",
            )
        elif accessory_watts < laptop_min:
            add(
                "Charging",
                "failed",
                f"The accessory provides up to {accessory_watts} W, below the "
                f"laptop's documented minimum input of {laptop_min} W.",
            )
        elif laptop_max is not None and accessory_watts < laptop_max:
            add(
                "Charging",
                "passed",
                f"The accessory's {accessory_watts} W meets the documented minimum input of {laptop_min} W.",
            )
            limitation = (
                f"Charging is limited to up to {accessory_watts} W; "
                f"the laptop lists support up to {laptop_max} W."
            )
            limits.append(limitation)
        else:
            add(
                "Charging",
                "passed",
                f"The accessory's {accessory_watts} W meets the laptop's documented charging input range.",
            )

    if failed:
        verdict = "incompatible"
        summary = (
            "At least one required capability is documented as unsupported or below the requested setup."
        )
    elif unknown:
        verdict = "insufficient_data"
        summary = (
            "Some required capabilities are not established by manufacturer "
            "specifications, so PortPilot will not guess."
        )
    elif limits:
        verdict = "compatible_with_limits"
        summary = "The requested setup is supported, with the documented limitation(s) listed below."
    else:
        verdict = "compatible"
        summary = "The requested setup is supported by the available specifications."

    return {
        "verdict": verdict,
        "summary": summary,
        "limits": limits,
        "requirements": checks,
        "evidence": laptop.get("evidence", []) + accessory.get("evidence", []),
        "rule_engine_version": RULE_ENGINE_VERSION,
    }
