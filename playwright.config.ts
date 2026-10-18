import { defineConfig } from '@playwright/test';
import { randomBytes } from 'node:crypto';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { resolve } from 'node:path';

const root = process.env.SPECBRIDGE_TEST_ROOT || __dirname;
const apiPort = Number(process.env.SPECBRIDGE_E2E_API_PORT || 8000);
const webPort = Number(process.env.SPECBRIDGE_E2E_WEB_PORT || 5173);
if (![apiPort, webPort].every(p => Number.isInteger(p) && p > 1023 && p < 65536) || apiPort === webPort) throw new Error('Use two distinct unprivileged fixture ports');
const apiOrigin = `http://127.0.0.1:${apiPort}`;
const webOrigin = `http://127.0.0.1:${webPort}`;
process.env.SPECBRIDGE_E2E_API_ORIGIN = apiOrigin;

// Inherited by workers and owned servers; never saved in browser storage or logs.
process.env.SPECBRIDGE_E2E_TOKEN ||= randomBytes(32).toString('hex');
process.env.SPECBRIDGE_E2E_DATA_DIR ||= mkdtempSync(resolve(tmpdir(), 'specbridge-browser-'));
process.env.SPECBRIDGE_TOKEN = process.env.SPECBRIDGE_E2E_TOKEN;
process.env.SPECBRIDGE_DATA_DIR = process.env.SPECBRIDGE_E2E_DATA_DIR;
const env = {
  SPECBRIDGE_TOKEN: process.env.SPECBRIDGE_TOKEN,
  SPECBRIDGE_DATA_DIR: process.env.SPECBRIDGE_DATA_DIR,
  SPECBRIDGE_PROVIDER: 'fixture',
  SPECBRIDGE_UI_ORIGIN: webOrigin,
  VITE_API_TARGET: apiOrigin,
  PYTHONPATH: resolve(root, 'services/api'),
};

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 45_000,
  use: { baseURL: webOrigin, trace: 'retain-on-failure' },
  webServer: [
    {
      command: `${resolve(root, '.venv/bin/python')} -m specbridge --port ${apiPort}`,
      cwd: root,
      env,
      url: `${apiOrigin}/api/health`,
      reuseExistingServer: false,
    },
    {
      command: `npm --prefix apps/web run dev -- --host 127.0.0.1 --port ${webPort} --strictPort`,
      cwd: root,
      env,
      url: webOrigin,
      reuseExistingServer: false,
    },
  ],
});
