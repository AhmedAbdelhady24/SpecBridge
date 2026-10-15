import { defineConfig } from '@playwright/test';
import { randomBytes } from 'node:crypto';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { resolve } from 'node:path';

const root = process.env.SPECBRIDGE_TEST_ROOT || __dirname;
// Inherited by workers and owned servers; never saved in browser storage or logs.
process.env.SPECBRIDGE_E2E_TOKEN ||= randomBytes(32).toString('hex');
process.env.SPECBRIDGE_E2E_DATA_DIR ||= mkdtempSync(resolve(tmpdir(), 'specbridge-browser-'));
process.env.SPECBRIDGE_TOKEN = process.env.SPECBRIDGE_E2E_TOKEN;
process.env.SPECBRIDGE_DATA_DIR = process.env.SPECBRIDGE_E2E_DATA_DIR;
const env = {
  SPECBRIDGE_TOKEN: process.env.SPECBRIDGE_TOKEN,
  SPECBRIDGE_DATA_DIR: process.env.SPECBRIDGE_DATA_DIR,
  SPECBRIDGE_PROVIDER: 'fixture',
  SPECBRIDGE_UI_ORIGIN: 'http://127.0.0.1:5173',
  PYTHONPATH: resolve(root, 'services/api'),
};

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 45_000,
  use: { baseURL: 'http://127.0.0.1:5173', trace: 'retain-on-failure' },
  webServer: [
    {
      command: `${resolve(root, '.venv/bin/python')} -m specbridge --port 8000`,
      cwd: root,
      env,
      url: 'http://127.0.0.1:8000/api/health',
      reuseExistingServer: false,
    },
    {
      command: 'npm --prefix apps/web run dev -- --host 127.0.0.1 --port 5173 --strictPort',
      cwd: root,
      env,
      url: 'http://127.0.0.1:5173',
      reuseExistingServer: false,
    },
  ],
});
