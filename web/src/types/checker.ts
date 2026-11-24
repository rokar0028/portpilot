export type Evidence = {
  id: string;
  capability_key: string;
  title: string;
  url: string;
  excerpt: string;
  checked_on: string;
  status: string;
};

export type Laptop = {
  id: string;
  name: string;
  model_code: string | null;
  usb_c_video_supported: boolean | null;
  usb_c_data_rate_gbps: number | null;
  usb_c_dp_version: string | null;
  usb_c_pd_input_min_w: number | null;
  usb_c_pd_input_max_w: number | null;
  evidence: Evidence[];
};

export type Accessory = {
  id: string;
  name: string;
  model_code: string | null;
  category: string;
  host_connection: string | null;
  requires_usb_c_dp_alt_mode: boolean | null;
  displaylink_supported?: boolean | null;
  hdmi_port_count: number | null;
  hdmi_max_resolution: string | null;
  hdmi_max_refresh_hz: number | null;
  pd_pass_through_max_w: number | null;
  usb_c_output_max_w: number | null;
  evidence: Evidence[];
};

export type Catalog = {
  laptops: Laptop[];
  accessories: Accessory[];
};

export type Requirement = {
  name: string;
  detail: string;
  status: "passed" | "failed" | "unknown";
};

export type Result = {
  verdict: string;
  evaluation_tier?: "verified" | "theoretical";
  summary: string;
  limits: string[];
  requirements: Requirement[];
  evidence: Evidence[];
  rule_engine_version: string;
};

export type Setup = {
  external_displays: number | null;
  resolution: string | null;
  refresh_rate_hz: number | null;
  laptop_charging: boolean | null;
};

export type ParsedSetup = {
  setup: Setup;
  needs_clarification: boolean;
  clarification_questions: string[];
  unsupported_requests: string[];
  notice: string;
};

export type CompatibleItem = {
  accessory: Accessory;
  verdict: string;
  evaluation_tier?: "verified" | "theoretical";
  summary: string;
  limits: string[];
};

export type CompatibleResponse = {
  laptop_id: string;
  laptop_name: string;
  total_evaluated: number;
  counts: Record<string, number>;
  results: CompatibleItem[];
};

export type SnapshotInfo = {
  id: string;
  createdAt: string;
  rulesVersion: string;
};
