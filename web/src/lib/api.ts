import type {
  Catalog,
  CompatibleResponse,
  ParsedSetup,
  Result,
  Setup,
} from "@/types/checker";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

async function request<T>(
  path: string,
  init?: RequestInit,
  fallbackMessage = "The PortPilot service could not complete this request.",
): Promise<T> {
  const response = await fetch(`${API}${path}`, init);
  const data = (await response.json().catch(() => null)) as
    | (T & {
        detail?: { message?: string };
      })
    | null;
  if (!response.ok) {
    throw new Error(data?.detail?.message ?? fallbackMessage);
  }
  return data as T;
}

export function loadCatalog(): Promise<Catalog> {
  return request<Catalog>("/devices");
}

export function runCompatibilityCheck(
  laptopId: string,
  accessoryId: string,
  setup: Setup,
): Promise<Result> {
  return request<Result>(
    "/checks",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        laptop_id: laptopId,
        accessory_id: accessoryId,
        setup,
      }),
    },
    "The compatibility service could not complete this check.",
  );
}

export function parseSetupDescription(
  description: string,
): Promise<ParsedSetup> {
  return request<ParsedSetup>("/setup-requests/parse", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ description }),
  });
}

export function loadCompatibleAccessories(
  laptopId: string,
  setup: Setup,
): Promise<CompatibleResponse> {
  const params = new URLSearchParams({
    displays: String(setup.external_displays ?? 1),
    resolution: setup.resolution ?? "1920x1080",
    refresh_rate_hz: String(setup.refresh_rate_hz ?? 60),
    laptop_charging: String(setup.laptop_charging ?? true),
  });
  return request<CompatibleResponse>(
    `/devices/laptops/${laptopId}/compatible-accessories?${params}`,
  );
}

export async function loadSnapshot(id: string): Promise<unknown | null> {
  const response = await fetch(
    `${API}/result-snapshots/${encodeURIComponent(id)}`,
  );
  if (!response.ok) return null;
  return response.json();
}

export { API };
