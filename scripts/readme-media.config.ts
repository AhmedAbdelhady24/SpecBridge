import { defineConfig } from '@playwright/test';
import base from '../playwright.config';

export default defineConfig(base, {
  testDir: '.',
  testMatch: 'readme-media.spec.ts',
  timeout: 180_000,
  use: {
    ...base.use,
    viewport: { width: 1440, height: 1000 },
    deviceScaleFactor: 1,
    trace: 'off',
    video: 'off',
    screenshot: 'off',
  },
});
