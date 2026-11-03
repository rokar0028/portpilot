import http from "k6/http";
import { check } from "k6";

const apiUrl = __ENV.PORTPILOT_API_URL ?? "http://127.0.0.1:18000";
const headers = { "Content-Type": "application/json" };

export const options = {
  scenarios: {
    parser_probe: {
      executor: "constant-arrival-rate",
      rate: 1,
      timeUnit: "1s",
      duration: __ENV.TEST_DURATION ?? "10s",
      preAllocatedVUs: 1,
      maxVUs: 5,
    },
  },
  thresholds: {
    // External LLM parser latency depends on external provider availability and is tracked separately from core deterministic API
    http_req_duration: ["p(95)<10000"],
  },
};

export default function () {
  const payload = {
    description: "I need to connect a Lenovo ThinkPad to dual 4K monitors and charge at 65W.",
  };
  const res = http.post(`${apiUrl}/setup-requests/parse`, JSON.stringify(payload), {
    headers,
    tags: { route: "/setup-requests/parse" },
  });

  check(res, {
    "parser responds (200 or 503)": (r) => r.status === 200 || r.status === 503,
  });
}
