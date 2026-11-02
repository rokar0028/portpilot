from typing import Any

from .schemas import CheckRequest

RULE_ENGINE_VERSION = "0.1.0"


def evaluate(request: CheckRequest, laptop: dict[str, Any], accessory: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, str]] = []
    failed = False
    unknown = False

    if request.setup.external_displays:
        host_video = laptop["ports"].get("usb_c_video")
        if not host_video:
            checks.append(
                {
                    "status": "failed",
                    "name": "USB-C video",
                    "detail": "The laptop has no documented USB-C video output.",
                }
            )
            failed = True
        elif not accessory["requirements"].get("host_usb_c_video"):
            checks.append(
                {
                    "status": "passed",
                    "name": "USB-C video",
                    "detail": "The accessory does not require USB-C video.",
                }
            )
        else:
            checks.append(
                {
                    "status": "passed",
                    "name": "USB-C video",
                    "detail": f"Laptop documentation lists {host_video}; the hub requires USB-C video.",
                }
            )

        max_displays = laptop["ports"].get("maximum_external_displays")
        if max_displays is None:
            checks.append(
                {
                    "status": "unknown",
                    "name": "Display count",
                    "detail": (
                        "The laptop source does not specify the maximum external display count "
                        "for this connection."
                    ),
                }
            )
            unknown = True
        elif request.setup.external_displays > max_displays:
            checks.append(
                {
                    "status": "failed",
                    "name": "Display count",
                    "detail": (
                        f"Requested {request.setup.external_displays} display(s), "
                        f"but the laptop supports {max_displays}."
                    ),
                }
            )
            failed = True
        else:
            checks.append(
                {
                    "status": "passed",
                    "name": "Display count",
                    "detail": f"Requested display count is within the documented limit of {max_displays}.",
                }
            )

        display_mode = laptop["ports"].get("display_mode_over_usb_c")
        requested_mode = f"{request.setup.resolution} at {request.setup.refresh_rate_hz} Hz"
        if display_mode is None:
            checks.append(
                {
                    "status": "unknown",
                    "name": "Display mode",
                    "detail": f"The laptop source does not confirm {requested_mode} over USB-C.",
                }
            )
            unknown = True
        elif display_mode != requested_mode:
            checks.append(
                {
                    "status": "failed",
                    "name": "Display mode",
                    "detail": f"The documented mode is {display_mode}; requested {requested_mode}.",
                }
            )
            failed = True
        else:
            checks.append(
                {
                    "status": "passed",
                    "name": "Display mode",
                    "detail": f"Laptop documentation supports {requested_mode}.",
                }
            )

    if request.setup.laptop_charging:
        laptop_pd = laptop["ports"].get("usb_c_power_delivery")
        hub_pd = accessory["outputs"].get("power_delivery_pass_through_watts")
        if laptop_pd is None or hub_pd is None:
            checks.append(
                {
                    "status": "unknown",
                    "name": "Charging",
                    "detail": (
                        "The available sources do not establish both laptop input and "
                        "hub pass-through requirements."
                    ),
                }
            )
            unknown = True
        else:
            checks.append(
                {
                    "status": "unknown",
                    "name": "Charging",
                    "detail": (
                        f"Laptop lists USB PD {laptop_pd}; hub passes through up to "
                        f"{hub_pd} W. Actual charging sufficiency for this configuration "
                        "is not confirmed."
                    ),
                }
            )
            unknown = True

    if failed:
        verdict = "incompatible"
        summary = "At least one required capability is documented as unsupported."
    elif unknown:
        verdict = "insufficient_data"
        summary = (
            "Some required capabilities are not established by the available manufacturer "
            "specifications, so PortPilot will not guess."
        )
    else:
        verdict = "compatible"
        summary = "The requested setup is supported by the available specifications."

    return {
        "verdict": verdict,
        "summary": summary,
        "limits": [],
        "requirements": checks,
        "evidence": laptop["evidence"] + accessory["evidence"],
        "rule_engine_version": RULE_ENGINE_VERSION,
    }
