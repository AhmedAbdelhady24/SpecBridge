# Documentation parser security fix — 2026-10-16

Status: implemented and verified. User authorized resolving the retained dependency risk. Live-model calls and remote publication remain outside this change.

The vulnerable chain was Starlight 0.42.6 → Expressive Code 0.44.2 → postcss-nested 6.2.0 → postcss-selector-parser 6.1.4. Current upstream Starlight/Expressive Code metadata still uses that chain. The [official advisory](https://github.com/advisories/GHSA-rj75-hqrm-r3gf) identifies 7.1.6 as the patched parser. Its earlier [7.0 changelog](https://github.com/postcss/postcss-selector-parser/blob/v7.0.0/CHANGELOG.md) documents an iteration/insertion change, so compatibility requires actual consumer checks.

The template now overrides only `postcss-nested@6.2.0`'s parser to exact version 7.1.6. The lock changes only the parser version, resolved tarball and integrity. Highlighter, nesting library and framework versions remain fixed. No advisory suppression or automatic forced upgrade is used. Remove the override after upstream supports a patched range, with fresh compatibility tests.

The export regression `test_exported_template_has_no_vulnerable_selector_parser` first failed on the original shipped lockfile and then passed on the patched lockfile. Four nesting transformations were recorded using the old installed consumer: ampersand/class/pseudo selectors, parent selector lists with child combinators, media with nested pseudo lists, and ancestor interpolation. The independent website checker now asserts those exact outputs against the installed exported dependency tree in both dev and preview modes. The fresh website install/build/navigation checks also exercise the template's real CSS pipeline.

Changing the template manifest, lockfile and README changes the template digest: existing candidate approvals cannot authorize a new package. Prepare and approve a fresh package. Previously exported ZIPs retain their original lockfile; replace them with a newly reviewed export or deliberately apply and review the same scoped dependency fix in their own repositories. SpecBridge never silently updates an existing exported repository.

Actual verification:

- Export dependency regression: RED on 6.1.4, GREEN on 7.1.6.
- Template `npm ci`, `npm run build`, `npm audit`: passed; zero known vulnerabilities (previously ten moderate entries from one advisory).
- Fresh exported package install/build/dev/preview, four CSS nesting compatibility assertions per server mode and seven-route Chromium checks: passed in 14.85 seconds with SpecBridge stopped. [Exact manifest/hash record](parser-fix-verification.json); local logs/screenshots in `/tmp/specbridge-parser-fixed-20261016-final`.
- Backend suite: 99 tests passed, plus documentation/source subtests. Ruff lint/format and strict mypy passed.
- Browser approval/security suite: 9/9 passed in 4.7 seconds. Existing template-change authorization tests remain green.
- CI now rejects moderate-or-higher documentation advisories. Hosted CI was not run.

 The original [first-slice verification](first-slice-results.md) and its JSON retain historical pre-fix hashes. A clean vulnerability audit checks known advisories; it is not a guarantee of no undiscovered vulnerabilities. CSS/configuration remain trusted source, and the scoped major-version override needs compatibility checks on later dependency updates.

Changed files: template manifest/lock/README, `scripts/check_docs.mjs`, export regression test, CI audit threshold and engineering evidence/plan. Used systematic debugging and verification-before-completion guidance. The lead implemented and ran all checks; an independent bounded security reviewer found no material issue. No runtime workflow or provider implementation changed. Next product task is [hosted-provider qualification planning](../plans/2026-10-16-hosted-provider-qualification.md).
