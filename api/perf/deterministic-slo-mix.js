import http from "k6/http";
import { check } from "k6";

const apiUrl = __ENV.PORTPILOT_API_URL ?? "http://127.0.0.1:18000";
const headers = { "Content-Type": "application/json" };

const warmupDuration = __ENV.WARMUP_DURATION ?? "10s";
const steadyDuration = __ENV.STEADY_STATE_DURATION ?? "30m";

export const options = {
  scenarios: {
    warmup: {
      executor: "constant-arrival-rate",
      rate: 5,
      timeUnit: "1s",
      duration: warmupDuration,
      preAllocatedVUs: 5,
      maxVUs: 20,
    },
    steady_state: {
      executor: "constant-arrival-rate",
      rate: 5,
      timeUnit: "1s",
      startTime: warmupDuration,
      duration: steadyDuration,
      preAllocatedVUs: 10,
      maxVUs: 50,
    },
  },
  thresholds: {
    "http_req_duration{scenario:steady_state}": ["p(95)<500"],
    "http_req_failed{scenario:steady_state}": ["rate<0.01"],
  },
};

const checksMix = [
  {
    name: "compatible",
    payload: {
      laptop_id: "e2e-good-laptop",
      accessory_id: "e2e-good-hub",
      setup: {
        external_displays: 1,
        resolution: "1920x1080",
        refresh_rate_hz: 60,
        laptop_charging: false,
      },
    },
    expectedVerdict: "compatible",
  },
  {
    name: "incompatible",
    payload: {
      laptop_id: "e2e-bad-laptop",
      accessory_id: "e2e-good-hub",
      setup: {
        external_displays: 1,
        resolution: "1920x1080",
        refresh_rate_hz: 60,
        laptop_charging: false,
      },
    },
    expectedVerdict: "incompatible",
  },
  {
    name: "insufficient_data",
    payload: {
      laptop_id: "e2e-unknown-laptop",
      accessory_id: "e2e-good-hub",
      setup: {
        external_displays: 1,
        resolution: "1920x1080",
        refresh_rate_hz: 60,
        laptop_charging: false,
      },
    },
    expectedVerdict: "insufficient_data",
  },
];

let checkIndex = 0;

export default function () {
  const rand = Math.random() * 100;

  if (rand < 40) {
    // 40% GET /devices
    const res = http.get(`${apiUrl}/devices`, { headers, tags: { route: "/devices" } });
    check(res, { "GET /devices status 200": (r) => r.status === 200 });
  } else if (rand < 70) {
    // 30% POST /checks (cycling supported, unsupported, insufficient-data)
    const checkCase = checksMix[checkIndex % checksMix.length];
    checkIndex++;
    const res = http.post(`${apiUrl}/checks`, JSON.stringify(checkCase.payload), {
      headers,
      tags: { route: "/checks", check_case: checkCase.name },
    });
    check(res, {
      "POST /checks status 200": (r) => r.status === 200,
      "POST /checks correct verdict": (r) => r.json("verdict") === checkCase.expectedVerdict,
    });
  } else if (rand < 80) {
    // 10% GET /devices/laptops/{device_id}
    const res = http.get(`${apiUrl}/devices/laptops/e2e-good-laptop`, {
      headers,
      tags: { route: "/devices/laptops/{device_id}" },
    });
    check(res, { "GET /devices/laptops status 200": (r) => r.status === 200 });
  } else if (rand < 90) {
    // 10% GET /devices/accessories/{device_id}
    const res = http.get(`${apiUrl}/devices/accessories/e2e-good-hub`, {
      headers,
      tags: { route: "/devices/accessories/{device_id}" },
    });
    check(res, { "GET /devices/accessories status 200": (r) => r.status === 200 });
  } else if (rand < 95) {
    // 5% GET /ready
    const res = http.get(`${apiUrl}/ready`, { headers, tags: { route: "/ready" } });
    check(res, { "GET /ready status 200": (r) => r.status === 200 });
  } else {
    // 5% POST /result-reports
    const reportPayload = {
      laptop_id: "e2e-good-laptop",
      accessory_id: "e2e-good-hub",
      setup: {
        external_displays: 1,
        resolution: "1920x1080",
        refresh_rate_hz: 60,
        laptop_charging: false,
      },
      verdict: "compatible",
      rule_engine_version: "0.3.0",
      note: "k6 load baseline evaluation report",
    };
    const res = http.post(`${apiUrl}/result-reports`, JSON.stringify(reportPayload), {
      headers,
      tags: { route: "/result-reports" },
    });
    check(res, { "POST /result-reports status 201": (r) => r.status === 201 });
  }
}
