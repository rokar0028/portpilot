# PortPilot — 90-Second Demo Outline

This is the recording script for the local app. The candidate outputs and manufacturer links were rechecked against the seeded database; record after a browser-accessible local stack or deployment is available.

## Candidate scenarios

### Supported setup

- Laptop: Lenovo IdeaPad Slim 5 15ARP10 (`lenovo-ideapad-slim-5-15arp10`)
- Accessory: Anker Nano USB-C Hub 7-in-1, model A83D2 (`anker-nano-hub-7in1-a83d2`)
- Setup: one 1080p display at 60 Hz, laptop charging enabled
- Expected from the current seed values: **Compatible**. The laptop lists USB-C video, 4K/60Hz, at least 45 W charging input, and up to three external displays; the hub lists DP Alt Mode host support, one HDMI output, and up to 85 W pass-through.
- Manufacturer sources: [Lenovo PSREF](https://psref.lenovo.com/Product/IdeaPad/IdeaPad_Slim_5_15ARP10), [Anker user guide](https://support.anker.com/s/article/Anker-Nano-USB-C-Hub-7-in-1-4K-HDMI-User-Guide-A83D2).

### Documented limitation that makes the request incompatible

- Use the same devices, request two external displays, and turn laptop charging off.
- Expected from the current seed values: **Incompatible**, because the hub documents one HDMI display output.
- Keep the laptop's total display limit and requested resolution the same so the failed requirement is visibly specific to the accessory.

## Recording sequence

| Time | Show |
| --- | --- |
| 0–10 sec | State the problem: confirm a laptop/accessory setup before buying, using manufacturer facts rather than guesses. |
| 10–25 sec | Select the devices and show the 1080p/60Hz plus charging request. |
| 25–45 sec | Run the check; pause on the verdict, requirement statuses, and capability-linked source excerpts. |
| 45–60 sec | Copy/open the shared result URL to show selections and setup are restored. |
| 60–78 sec | Change to two displays with charging off; run the check and show the accessory output-count failure. |
| 78–90 sec | Close on the coverage page, verified catalogue counts, and the rule that missing specifications remain unknown. |

## Pre-recording checklist

- [x] Complete Phase 6 source review and run the API/frontend quality commands.
- [x] Confirm the compatible and incompatible outputs with the current seeded database and inspect the manufacturer source links.
- [ ] Use a clean browser window without tokens, admin pages, or personal information.
- [ ] Record at 1080p, keep text and evidence readable, and trim pauses while preserving the full result explanations.
- [ ] Review the exported video and confirm it is no longer than 90 seconds.
