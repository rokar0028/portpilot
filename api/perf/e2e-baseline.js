import http from "k6/http";
import { check, sleep } from "k6";

const apiUrl = __ENV.PORTPILOT_API_URL ?? "http://127.0.0.1:18000";
const headers = { "Content-Type": "application/json" };

export const options = {
  vus: 2,
  duration: "30s",
};

export default function () {
  const catalogue = http.get(`${apiUrl}/devices`);
  check(catalogue, {
    "catalogue responds successfully": (response) => response.status === 200,
  });

  const result = http.post(
    `${apiUrl}/checks`,
    JSON.stringify({
      laptop_id: "e2e-good-laptop",
      accessory_id: "e2e-good-hub",
      setup: {
        external_displays: 1,
        resolution: "1920x1080",
        refresh_rate_hz: 60,
        laptop_charging: false,
      },
    }),
    { headers },
  );
  check(result, {
    "compatibility check responds successfully": (response) => response.status === 200,
    "compatibility check uses a supported fixture": (response) =>
      response.json("verdict") === "compatible",
  });

  sleep(1);
}
