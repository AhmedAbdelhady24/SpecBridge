import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { chromium } from '@playwright/test';

const [base, directory] = process.argv.slice(2);
assert.equal(new URL(base).hostname, '127.0.0.1');
// Guard the consumer-scoped parser override against CSS nesting regressions.
const packageRequire = createRequire(join(directory, 'package.json'));
const postcss = packageRequire('postcss');
const nested = packageRequire('postcss-nested');
const cssCases = [
  {
    input: ".a { &.active, &:hover { color: red } }",
    output: ".a.active, .a:hover { color: red }"
  },
  {
    input: ".a, .b { > .child { color: blue } }",
    output: ".a > .child, .b > .child { color: blue }"
  },
  {
    input: ".a { @media (width > 30em) { &:is(.b, .c) { color: red } } }",
    output: "@media (width > 30em) { .a:is(.b, .c) { color: red } }"
  },
  {
    input: ".a { .b & { color: red } }",
    output: ".b .a { color: red }"
  }
];
for (const { input, output } of cssCases) {
  assert.equal((await postcss([nested()]).process(input, { from: undefined })).css, output);
}
const snapshot = JSON.parse(await readFile(join(directory, 'revision.json'), 'utf8'));
const browser = await chromium.launch({
  headless: true,
  args: ['--disable-gpu', '--disable-features=CDPScreenshotNewSurface']
});
try {
  const page = await browser.newPage();
  const remote = [];
  await page.route('**/*', async (route) => {
    if (new URL(route.request().url()).origin !== new URL(base).origin) {
      remote.push(route.request().url());
      await route.abort();
    } else await route.continue();
  });
  await page.goto(base, { waitUntil: 'networkidle' });
  assert.ok((await page.locator('h1').textContent()).includes(snapshot.artifact.title));
  assert.equal(await page.locator('main script, main img, #attack-title, #attack-body').count(), 0);
  assert.equal(await page.locator('main a[href^="javascript:"], main a[href^="data:"]').count(), 0);
  for (const slug of ['requirements', 'stories', 'edge-cases', 'risks', 'questions', 'provenance', 'decisions']) {
    const response = await page.goto(`${base}/${slug}/`, { waitUntil: 'networkidle' });
    assert.equal(response.status(), 200, slug);
    if (slug === 'decisions') {
      const body = await page.locator('main').textContent();
      assert.ok(snapshot.decisions.questions.length > 0, 'Export exercise must include a real saved answer');
      for (const question of snapshot.decisions.questions) {
        assert.ok(body.includes(question.text));
        assert.ok(body.includes(question.latest_answer.text));
      }
    }
    if (slug === 'requirements') {
      for (const [index, requirement] of snapshot.artifact.requirements.entries()) {
        assert.equal(await page.getByRole('heading', { name: `Requirement ${index + 1}`, exact: true }).count(), 1);
        assert.ok((await page.locator('main').textContent()).includes(requirement.text));
      }
      for (const link of await page.locator('main a[href*="stories/#"]').all()) {
        const target = new URL(await link.getAttribute('href'), page.url());
        const targetResponse = await page.request.get(target.href.split('#')[0]);
        assert.equal(targetResponse.status(), 200);
        assert.ok((await targetResponse.text()).includes(`id="${target.hash.slice(1)}"`));
      }
    }
  }
  assert.deepEqual(remote, [], 'Documentation must not request remote assets');
  await page.close();
  const shotPage = await browser.newPage();
  await shotPage.goto(base, { waitUntil: 'networkidle' });
  try {
    await shotPage.screenshot({ path: join(directory, `website-${new URL(base).port}.png`), timeout: 2000 });
  } catch {
    // Non-fatal if headless compositor screenshot times out in background daemon environments
  }
  console.log(JSON.stringify({ website: base, navigation: 'passed', attack_content: 'inert', remote_requests: 0 }));
} finally {
  await browser.close();
}
