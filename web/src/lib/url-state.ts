import type { Accessory, Laptop, Setup } from "@/types/checker";

export const defaultSetup: Setup = {
  external_displays: 1,
  resolution: "1920x1080",
  refresh_rate_hz: 60,
  laptop_charging: true,
};

function parseNumber(
  value: string | null,
  min: number,
  max: number,
): number | null {
  if (!value || value === "null" || Number.isNaN(Number(value))) return null;
  const number = Number(value);
  return number >= min && number <= max ? number : null;
}

export function restoreSelectionState(
  params: URLSearchParams,
  laptops: Laptop[],
  accessories: Accessory[],
): { laptopId: string; accessoryId: string; setup: Setup } {
  const laptop = params.get("laptop");
  const accessory = params.get("accessory");
  const rawResolution = params.get("resolution");
  return {
    laptopId: laptops.some((item) => item.id === laptop) ? (laptop ?? "") : "",
    accessoryId: accessories.some((item) => item.id === accessory)
      ? (accessory ?? "")
      : "",
    setup: {
      external_displays: params.has("displays")
        ? parseNumber(params.get("displays"), 0, 8)
        : defaultSetup.external_displays,
      resolution: params.has("resolution")
        ? rawResolution &&
          rawResolution !== "null" &&
          rawResolution.length <= 30
          ? rawResolution
          : null
        : defaultSetup.resolution,
      refresh_rate_hz: params.has("refresh")
        ? parseNumber(params.get("refresh"), 24, 240)
        : defaultSetup.refresh_rate_hz,
      laptop_charging: params.has("charging")
        ? params.get("charging") === "true"
          ? true
          : params.get("charging") === "false"
            ? false
            : null
        : defaultSetup.laptop_charging,
    },
  };
}

export function buildResultUrl(
  currentUrl: string,
  laptopId: string,
  accessoryId: string,
  setup: Setup,
): string {
  const url = new URL(currentUrl);
  url.search = new URLSearchParams({
    laptop: laptopId,
    accessory: accessoryId,
    displays: String(setup.external_displays),
    resolution: String(setup.resolution),
    refresh: String(setup.refresh_rate_hz),
    charging: String(setup.laptop_charging),
  }).toString();
  return url.toString();
}
