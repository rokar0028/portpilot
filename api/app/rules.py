import re
from typing import Any

from .schemas import CheckRequest

RULE_ENGINE_VERSION = "0.6.0"


def _normalize_resolution(value: str) -> str:
    normalized = value.strip().lower()
    aliases = {
        "4k": "3840x2160",
        "uhd": "3840x2160",
        "4k uhd": "3840x2160",
        "4k-uhd": "3840x2160",
        "1080p": "1920x1080",
        "fhd": "1920x1080",
        "1440p": "2560x1440",
        "qhd": "2560x1440",
        "2k": "2560x1440",
        "5k": "5120x2880",
        "6k": "6016x3384",
        "8k": "7680x4320",
    }
    aliased = aliases.get(normalized, normalized)
    match = re.fullmatch(r"(\d{3,5})\s*x\s*(\d{3,5})", aliased)
    if match:
        return f"{match.group(1)}x{match.group(2)}"
    return aliased


def _mode_at_least(
    maximum_resolution: str | None,
    maximum_refresh: int | None,
    requested_resolution: str | None,
    requested_refresh: int | None,
) -> bool | None:
    """Return whether a maximum display mode covers the request, or None if unknown."""
    if (
        maximum_resolution is None
        or maximum_refresh is None
        or requested_resolution is None
        or requested_refresh is None
    ):
        return None

    def dimensions(value: str) -> tuple[int, int] | None:
        normalized = _normalize_resolution(value)
        match = re.fullmatch(r"(\d{3,5})x(\d{3,5})", normalized)
        return (int(match.group(1)), int(match.group(2))) if match else None

    requested = dimensions(requested_resolution)
    maximum = dimensions(maximum_resolution)
    if requested is None or maximum is None:
        return None
    return requested[0] <= maximum[0] and requested[1] <= maximum[1] and requested_refresh <= maximum_refresh


def _configuration_match(
    configurations: list[dict[str, Any]] | None, requested: list[Any], topology: str | None
) -> bool | None:
    """Match only a manufacturer-documented simultaneous display configuration."""
    if not configurations or not requested:
        return None

    def mode_tuple(mode: Any) -> tuple[str, int, str | None]:
        if isinstance(mode, dict):
            resolution, refresh = mode.get("resolution"), mode.get("refresh_rate_hz")
            connection = mode.get("connection")
        else:
            resolution, refresh = mode.resolution, mode.refresh_rate_hz
            connection = mode.connection
        return (
            _normalize_resolution(str(resolution)),
            int(refresh),
            connection.strip().casefold() if connection else None,
        )

    req_tuples = [mode_tuple(m) for m in requested]

    for configuration in configurations:
        doc_displays = configuration.get("displays", [])
        if len(doc_displays) != len(req_tuples):
            continue
        documented_topology = configuration.get("topology")
        if topology is not None and documented_topology is None:
            continue
        if topology is not None and documented_topology.strip().casefold() != topology.strip().casefold():
            continue

        doc_tuples = [mode_tuple(m) for m in doc_displays]

        unmatched_doc = list(doc_tuples)
        matched_all = True
        for req_res, req_hz, req_conn in req_tuples:
            found_idx = None
            for idx, (doc_res, doc_hz, doc_conn) in enumerate(unmatched_doc):
                if req_res == doc_res and req_hz == doc_hz:
                    if req_conn is None or doc_conn is None or req_conn == doc_conn:
                        found_idx = idx
                        break
            if found_idx is not None:
                unmatched_doc.pop(found_idx)
            else:
                matched_all = False
                break

        if matched_all:
            return True
    return None


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
    requested_count = len(setup.displays) if setup.displays is not None else setup.external_displays
    requested_resolution = (
        setup.displays[0].resolution
        if setup.displays is not None and len(setup.displays) == 1
        else setup.resolution
    )
    requested_refresh = (
        setup.displays[0].refresh_rate_hz
        if setup.displays is not None and len(setup.displays) == 1
        else setup.refresh_rate_hz
    )
    ports = laptop["ports"]
    outputs = accessory["outputs"]
    requirements = accessory["requirements"]

    # A connection is required for every setup. The initial catalogue models USB-C hosts.
    host = (accessory.get("host_connection") or "").lower()
    if any(token in host for token in ("usb-c", "usb c", "thunderbolt", "usb4")):
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

    if requested_count is None:
        add("Display count", "unknown", "The requested external display count is not established.")
    elif requested_count:
        is_charger = accessory.get("category") == "usb_c_charger"
        is_displaylink = requirements.get("displaylink_supported") is True
        dp_required = requirements.get("host_usb_c_video")
        if is_charger:
            add(
                "USB-C video",
                "failed",
                "The accessory is a charger and does not support video output.",
            )
        elif is_displaylink:
            add(
                "USB-C video",
                "passed",
                "The accessory uses DisplayLink USB graphics; native DisplayPort Alt Mode is not required.",
            )
            limits.append(
                "DisplayLink video output requires the DisplayLink driver/manager software to be installed "
                "on the host operating system."
            )
        elif dp_required is True:
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
        if is_displaylink:
            if laptop_display_limit is not None and requested_count > laptop_display_limit:
                add(
                    "Display count",
                    "passed",
                    "DisplayLink virtual displays are driven by software and bypass the laptop's native GPU "
                    f"limit of {laptop_display_limit} display(s).",
                )
                limits.append(
                    "DisplayLink virtual displays bypass native GPU display limits but require host "
                    "software drivers and increase CPU utilization."
                )
            elif laptop_display_limit is not None:
                add(
                    "Display count",
                    "passed",
                    f"Requested display count is within the laptop limit of {laptop_display_limit}.",
                )
            else:
                add(
                    "Display count",
                    "passed",
                    "DisplayLink virtual displays are driven by software over USB data and bypass native "
                    "GPU display limits.",
                )
        elif laptop_display_limit is None:
            add(
                "Display count",
                "unknown",
                "The laptop source does not specify its maximum external display count.",
            )
        elif requested_count > laptop_display_limit:
            add(
                "Display count",
                "failed",
                f"Requested {requested_count} displays; the laptop supports up to {laptop_display_limit}.",
            )
        else:
            add(
                "Display count",
                "passed",
                f"Requested display count is within the laptop limit of {laptop_display_limit}.",
            )

        is_display = accessory.get("category") in {"portable_monitor", "external_display"}
        config_display_max = (
            max(
                (len(cfg.get("displays", [])) for cfg in outputs.get("display_configurations") or []),
                default=0,
            )
            if outputs.get("display_configurations")
            else 0
        )
        accessory_display_limit = (
            0
            if is_charger
            else 1
            if is_display
            else max(outputs.get("display_count") or 0, config_display_max)
            if (outputs.get("display_count") is not None or config_display_max > 0)
            else None
        )
        if accessory_display_limit is None:
            add(
                "Accessory display outputs",
                "unknown",
                "The accessory source does not establish its usable display output count.",
            )
        elif requested_count > accessory_display_limit:
            if is_charger:
                add(
                    "Accessory display outputs",
                    "failed",
                    (
                        "The accessory is a charger and provides 0 display outputs; "
                        f"requested {requested_count} displays."
                    ),
                )
            elif is_display:
                add(
                    "Accessory display outputs",
                    "failed",
                    (
                        "The accessory is a single display and provides 1 screen; "
                        f"requested {requested_count} displays."
                    ),
                )
            else:
                add(
                    "Accessory display outputs",
                    "failed",
                    (
                        f"Requested {requested_count} displays; "
                        f"the accessory provides {accessory_display_limit}."
                    ),
                )
        else:
            if is_display:
                add(
                    "Accessory display outputs",
                    "passed",
                    "The accessory provides 1 display screen.",
                )
            else:
                add(
                    "Accessory display outputs",
                    "passed",
                    f"The accessory has enough documented outputs ({accessory_display_limit}).",
                )

        os_name = (laptop.get("operating_system") or "").strip().lower()
        is_macos = "macos" in os_name or "os x" in os_name or os_name.startswith("mac")
        host_conn = (accessory.get("host_connection") or "").strip().lower()
        is_thunderbolt = "thunderbolt" in host_conn or "usb4" in host_conn
        acc_display_count = outputs.get("display_count") or 0

        multi_display_requested = requested_count is not None and requested_count > 1
        multi_port_extended_requested = (
            setup.display_topology == "extended"
            and not is_charger
            and not is_display
            and acc_display_count > 1
        )

        should_evaluate_mst = (
            (multi_display_requested or multi_port_extended_requested)
            and is_macos
            and not is_charger
            and not is_display
        )
        if should_evaluate_mst:
            if is_thunderbolt:
                add(
                    "Display topology (MST)",
                    "passed",
                    "macOS supports multiple independent external displays over Thunderbolt / USB4.",
                )
            elif is_displaylink:
                add(
                    "Display topology (MST)",
                    "passed",
                    "macOS supports multiple independent extended displays via DisplayLink without "
                    "DisplayPort MST.",
                )
                limits.append(
                    "On macOS, DisplayLink requires the DisplayLink Manager application to provide "
                    "multiple extended displays."
                )
            else:
                topology = setup.display_topology.strip().lower() if setup.display_topology else None
                if topology == "extended":
                    if requested_count == 1:
                        add(
                            "Display topology (MST)",
                            "passed",
                            "macOS supports one independent extended display over standard USB-C. "
                            "Additional displays connected to this hub will mirror.",
                        )
                        limits.append(
                            "On macOS, this multi-port hub supports only one independent extended display "
                            "over standard USB-C; connecting a second display will mirror the first "
                            "(macOS does not support DisplayPort MST)."
                        )
                    else:
                        add(
                            "Display topology (MST)",
                            "failed",
                            "macOS does not support DisplayPort Multi-Stream Transport (MST) over "
                            "standard USB-C; multiple external displays cannot be extended independently.",
                        )
                else:
                    add(
                        "Display topology (MST)",
                        "passed",
                        "Multiple external displays over standard USB-C will mirror each other on macOS.",
                    )
                    limits.append(
                        "On macOS, multiple external displays over standard USB-C DisplayPort Alt Mode "
                        "mirror each other (macOS does not support DisplayPort MST)."
                    )

        dp_version = ports.get("usb_c_dp_version")
        if (
            dp_version == "1.2"
            and not is_thunderbolt
            and not is_displaylink
            and accessory.get("category") in {"usb_c_hub", "usb_c_dock"}
        ):
            norm_res = _normalize_resolution(requested_resolution) if requested_resolution else ""
            if norm_res == "3840x2160" and requested_refresh and requested_refresh >= 60:
                add(
                    "Display bandwidth (lane allocation)",
                    "passed",
                    "DisplayPort 1.2 with active USB 3.0 data is limited to 2 video lanes, "
                    "capping 4K refresh rate to 30 Hz.",
                )
                limits.append(
                    "DisplayPort 1.2 hosts require 4 full video lanes for 4K at 60 Hz; "
                    "hubs providing USB 3.0 data speeds reduce video to 2 lanes, "
                    "limiting output to 4K at 30 Hz."
                )

        data_rate = ports.get("usb_c_data_rate_gbps")
        if (
            data_rate is not None
            and not is_displaylink
            and accessory.get("category") in {"usb_c_hub", "usb_c_dock"}
        ):
            norm_res = _normalize_resolution(requested_resolution) if requested_resolution else ""
            is_high_res = norm_res in {"3840x2160", "5120x2880", "6016x3384", "7680x4320"}
            has_data_ports = bool(outputs.get("usb_a_port_count") or outputs.get("ethernet_max_gbps"))
            if data_rate <= 5 and is_high_res and has_data_ports:
                limits.append(
                    f"Host USB-C port is {data_rate} Gbps (USB 3.2 Gen 1); driving high-resolution "
                    "video while using USB data ports shares physical bus bandwidth, which may limit "
                    "refresh rates or throttle peripheral speeds."
                )
            elif data_rate <= 10 and norm_res in {"5120x2880", "6016x3384", "7680x4320"}:
                limits.append(
                    f"Host USB-C data rate is {data_rate} Gbps; ultra-high resolutions "
                    f"({requested_resolution}) may require Display Stream Compression (DSC) or reduce "
                    "available peripheral data bandwidth."
                )

        combined_modes_requested = setup.displays is not None and (
            len(setup.displays) > 1 or setup.display_topology is not None
        )

        if is_displaylink and not combined_modes_requested:
            add(
                "Laptop display mode",
                "passed",
                "DisplayLink renders video via host software over USB data; "
                "laptop DisplayPort Alt Mode limits do not apply.",
            )
        else:
            if dp_required is True:
                laptop_resolution = ports.get("usb_c_max_resolution")
                laptop_refresh = ports.get("usb_c_max_refresh_hz")
            elif dp_required is False:
                laptop_resolution = None
                laptop_refresh = None
            else:
                laptop_resolution = None
                laptop_refresh = None
            laptop_mode_ok = (
                None
                if combined_modes_requested
                else _mode_at_least(
                    laptop_resolution, laptop_refresh, requested_resolution, requested_refresh
                )
            )
            if laptop_mode_ok is None and not combined_modes_requested:
                add(
                    "Laptop display mode",
                    "unknown",
                    "The laptop source does not establish the maximum mode for this display path.",
                )
            elif laptop_mode_ok and not combined_modes_requested:
                add(
                    "Laptop display mode",
                    "passed",
                    f"The laptop supports at least {requested_resolution} at "
                    f"{requested_refresh} Hz on this path.",
                )
            elif not combined_modes_requested:
                add(
                    "Laptop display mode",
                    "failed",
                    f"The requested {requested_resolution} at {requested_refresh} Hz "
                    "exceeds the laptop's documented maximum.",
                )

            if dp_required is False and not combined_modes_requested:
                checks[-1]["detail"] = (
                    "The accessory does not require DisplayPort Alt Mode, but its alternate video path "
                    "from the laptop is not modeled."
                )

        if is_charger and not combined_modes_requested:
            add(
                "Accessory display mode",
                "failed",
                "The accessory is a charger and does not provide display outputs.",
            )
        else:
            accessory_mode_ok = (
                None
                if combined_modes_requested
                else _mode_at_least(
                    outputs.get("hdmi_max_resolution"),
                    outputs.get("hdmi_max_refresh_hz"),
                    requested_resolution,
                    requested_refresh,
                )
            )
            if accessory_mode_ok is None and not combined_modes_requested:
                add(
                    "Accessory display mode",
                    "unknown",
                    "The accessory source does not establish a maximum mode for its display output.",
                )
            elif accessory_mode_ok and not combined_modes_requested:
                add(
                    "Accessory display mode",
                    "passed",
                    f"The accessory supports at least {requested_resolution} at {requested_refresh} Hz.",
                )
            elif not combined_modes_requested:
                add(
                    "Accessory display mode",
                    "failed",
                    f"The requested {requested_resolution} at {requested_refresh} Hz "
                    "exceeds the accessory's documented maximum.",
                )

        if combined_modes_requested:
            for label, configurations in (
                ("Laptop", ports.get("display_configurations")),
                ("Accessory", outputs.get("display_configurations")),
            ):
                if label == "Accessory" and is_charger:
                    add(
                        "Accessory combined display mode",
                        "failed",
                        "The accessory is a charger and does not provide display outputs.",
                    )
                    continue
                if label == "Accessory" and is_display:
                    add(
                        "Accessory combined display mode",
                        "failed",
                        "The accessory is a single display and cannot support "
                        "multiple simultaneous displays.",
                    )
                    continue
                if label == "Laptop" and is_displaylink:
                    add(
                        "Laptop combined display mode",
                        "passed",
                        "DisplayLink renders simultaneous displays via host software over USB data; "
                        "laptop DisplayPort Alt Mode configurations do not apply.",
                    )
                    continue
                if label == "Laptop" and dp_required is False:
                    add(
                        "Laptop combined display mode",
                        "unknown",
                        "The accessory does not require DisplayPort Alt Mode, but its alternate video path "
                        "from the laptop is not modeled.",
                    )
                    continue
                if label == "Laptop" and dp_required is None:
                    add(
                        "Laptop combined display mode",
                        "unknown",
                        "The accessory source does not establish whether USB-C video is required; "
                        "simultaneous display configuration from the laptop cannot be verified.",
                    )
                    continue
                combined_match = _configuration_match(
                    configurations, setup.displays or [], setup.display_topology
                )
                if combined_match:
                    add(
                        f"{label} combined display mode",
                        "passed",
                        "The documented simultaneous configuration supports all "
                        f"{requested_count} requested display modes.",
                    )
                else:
                    topology_note = (
                        f" and topology '{setup.display_topology}'" if setup.display_topology else ""
                    )
                    add(
                        f"{label} combined display mode",
                        "unknown",
                        f"The available source does not establish {requested_count} simultaneous displays "
                        f"at the requested modes{topology_note}; individual maxima do not establish "
                        "aggregate bandwidth or lane allocation.",
                    )
        elif requested_count > 1:
            if is_displaylink:
                add(
                    "Combined display mode",
                    "passed",
                    "DisplayLink handles multiple displays via host software compression over USB data "
                    "without DisplayPort lane allocation constraints.",
                )
            elif is_thunderbolt and (laptop_display_limit is None or requested_count <= laptop_display_limit):
                add(
                    "Combined display mode",
                    "passed",
                    f"Thunderbolt / USB4 architecture provides dedicated multi-stream bandwidth "
                    f"for up to {laptop_display_limit or requested_count} independent displays.",
                )
            else:
                add(
                    "Combined display mode",
                    "unknown",
                    "The request specifies a display count but not each simultaneous mode; the sources "
                    "do not establish the combined configuration, aggregate bandwidth, or lane allocation.",
                )

    if setup.laptop_charging is None:
        add("Charging", "unknown", "Whether laptop charging is required is not established.")
    elif setup.laptop_charging:
        laptop_min = ports.get("usb_c_pd_input_min_w")
        laptop_max = ports.get("usb_c_pd_input_max_w")
        accessory_watts = outputs.get("charging_output_watts")
        hub_input_watts = accessory.get("pd_input_max_w")

        overhead_note = ""
        if hub_input_watts is not None and accessory_watts is not None and hub_input_watts > accessory_watts:
            overhead = hub_input_watts - accessory_watts
            overhead_note = f" (after {overhead} W hub reservation from {hub_input_watts} W input)"

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
                f"The accessory provides up to {accessory_watts} W{overhead_note}, below the "
                f"laptop's documented minimum input of {laptop_min} W.",
            )
        elif laptop_max is not None and accessory_watts < laptop_max:
            add(
                "Charging",
                "passed",
                f"The accessory's {accessory_watts} W{overhead_note} meets the documented "
                f"minimum input of {laptop_min} W.",
            )
            limitation = (
                f"Charging is limited to up to {accessory_watts} W{overhead_note}; "
                f"the laptop lists support up to {laptop_max} W."
            )
            limits.append(limitation)
        else:
            add(
                "Charging",
                "passed",
                f"The accessory's {accessory_watts} W{overhead_note} meets the laptop's "
                "documented charging input range.",
            )

    is_theoretical = (
        laptop.get("brand") == "Standard Protocol"
        or accessory.get("brand") == "Standard Protocol"
        or str(laptop.get("id", "")).startswith("protocol-")
        or str(accessory.get("id", "")).startswith("protocol-")
        or getattr(request, "evaluation_tier", None) == "theoretical"
    )
    evaluation_tier = "theoretical" if is_theoretical else "verified"

    if is_theoretical:
        if failed:
            verdict = "incompatible"
            summary = (
                "The requested setup exceeds the bandwidth, power, or topology limits "
                "of the selected standard protocol specifications."
            )
        elif unknown:
            verdict = "insufficient_data"
            summary = (
                "Certain setup requirements are outside the baseline capabilities "
                "defined for this protocol profile."
            )
        elif limits:
            verdict = "compatible_with_limits"
            summary = (
                "The requested setup is theoretically supported under standard "
                "protocol specifications, with documented limitations."
            )
        else:
            verdict = "compatible"
            summary = (
                "The requested setup is theoretically supported under standard "
                "hardware protocol specifications."
            )
    else:
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
        "evaluation_tier": evaluation_tier,
        "summary": summary,
        "limits": limits,
        "requirements": checks,
        "evidence": laptop.get("evidence", []) + accessory.get("evidence", []),
        "rule_engine_version": RULE_ENGINE_VERSION,
    }
