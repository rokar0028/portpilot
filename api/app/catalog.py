from typing import Any

CATALOG: dict[str, dict[str, Any]] = {
    "laptops": {
        "lenovo-ideapad-slim-3-14irh10r": {
            "id": "lenovo-ideapad-slim-3-14irh10r",
            "name": "Lenovo IdeaPad Slim 3 14IRH10R",
            "brand": "Lenovo",
            "ports": {
                "usb_c_video": "DisplayPort 1.2",
                "usb_c_power_delivery": "45–65 W",
                "maximum_external_displays": None,
                "display_mode_over_usb_c": None,
            },
            "evidence": [
                {
                    "title": "Lenovo PSREF: IdeaPad Slim 3 14IRH10R",
                    "url": "https://psref.lenovo.com/Product/IdeaPad/IdeaPad_Slim_3_14IRH10R",
                    "excerpt": (
                        "1x USB-C (USB 5Gbps / USB 3.2 Gen 1), with USB PD 45-65W and DisplayPort 1.2."
                    ),
                    "checked_on": "2026-11-02",
                    "status": "verified",
                }
            ],
        }
    },
    "accessories": {
        "anker-364-usb-c-hub": {
            "id": "anker-364-usb-c-hub",
            "name": "Anker 364 USB-C Hub (10-in-1, Dual 4K HDMI)",
            "brand": "Anker",
            "category": "USB-C hub",
            "requirements": {"host_usb_c_video": True},
            "outputs": {
                "hdmi": "up to 4K (3840 × 2160) at 60 Hz",
                "power_delivery_pass_through_watts": 85,
            },
            "evidence": [
                {
                    "title": "Anker 364 USB-C Hub product specifications",
                    "url": "https://service.anker.com/product-description/a085g000004zuplAAA",
                    "excerpt": (
                        "PD input up to 100 W; 85 W maximum PD pass-through. HDMI outputs up to 4K at 60 Hz."
                    ),
                    "checked_on": "2026-11-02",
                    "status": "verified",
                }
            ],
        }
    },
}


def list_devices(kind: str) -> list[dict[str, Any]]:
    return list(CATALOG[kind].values())
