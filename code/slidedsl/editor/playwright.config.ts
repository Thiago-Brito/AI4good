import { defineConfig } from "@playwright/test";
import path from "node:path";
import fs from "node:fs";

const root = path.resolve("..");
const python = path.join(
  root,
  ".venv",
  process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
);
const chrome = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const browser =
  process.env.SLIDEDSL_BROWSER ??
  (process.platform === "win32" && fs.existsSync(chrome) ? chrome : undefined);
export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  timeout: 45000,
  outputDir: "../outputs/ui-tests",
  reporter: [
    ["list"],
    ["json", { outputFile: "../outputs/ui-tests/results.json" }],
  ],
  use: {
    baseURL: "http://127.0.0.1:5173",
    headless: true,
    viewport: { width: 1440, height: 1100 },
    launchOptions: browser ? { executablePath: browser } : {},
    screenshot: "only-on-failure",
  },
  webServer: [
    {
      command: `"${python}" -m uvicorn slidedsl.server:app --host 127.0.0.1 --port 8000`,
      cwd: root,
      url: "http://127.0.0.1:8000/api/health",
      timeout: 30000,
      reuseExistingServer: !process.env.CI,
    },
    {
      command: "npm run dev",
      url: "http://127.0.0.1:5173",
      timeout: 30000,
      reuseExistingServer: !process.env.CI,
    },
  ],
});
