# Documentation parser security fix

Authorized: user requested removal of the remaining dependency risk on 2026-10-16. Scope: documentation template manifest/lock, export regression, affected documentation and verification evidence. No provider calls, project-data migrations or remote writes.

Cause: Starlight 0.42.6 → Expressive Code 0.44.2 → postcss-nested 6.2.0 → selector-parser 6.1.4. Current upstream metadata still requires this vulnerable parser range. GHSA-rj75-hqrm-r3gf is fixed in 7.1.6. Parser 7's documented major change concerns safe insertion during iteration; inspect the consumer and compare real generated CSS rather than assume compatibility.

- [x] Reproduce the vulnerable lock/audit with a failing export dependency regression.
- [x] Record a baseline trusted CSS/nesting transformation, then apply only a consumer-scoped exact parser override to 7.1.6. Leave the highlighter/nesting framework versions unchanged.
- [x] Clean-install and audit the template, verify CSS transformation compatibility, clean independent export install/build/dev/preview and backend/browser regressions. If compatibility fails, remove the override and reassess; do not suppress the advisory.
- [x] Update current documentation and record exact checks, source links, residual override maintenance and approval invalidation. Preserve historical pre-fix evidence. Review diff and commit locally.

Success: no affected parser in the shipped lockfile; npm audit reports zero vulnerabilities; exported packages preserve the fix and build/view independently. Existing approvals must become stale because template bytes change. This does not qualify live-model output.

Verified: parser export regression RED→GREEN; 99 backend tests and 9 browser cases green; clean template and exported installs/build/dev/preview plus four CSS compatibility cases passed. Template audit reports zero known vulnerabilities. See [the final report](../evaluations/parser-security-fix.md). Independent bounded security review found no material issue.
