<!-- codebase-memory-mcp:start -->
For structural codebase exploration, use the installed `codebase-memory` skill.
<!-- codebase-memory-mcp:end -->

# SpecBridge engineering

Purpose: turn product ideas and project evidence into validated requirements, reviewed backlog proposals, and Git-backed documentation that developers can use independently.

## Current state and paths

- Technical first slice implemented: local FastAPI/SQLite workflow, React review UI and standalone Starlight export. Fixture/browser verification is separate from pending semantic, live-provider and unfamiliar-human acceptance. See `docs/evaluations/first-slice-results.md` for current evidence and limits.
- `services/api/specbridge/`: backend security, contracts, persistence, knowledge, skills, providers, workflow and publication.
- Milestone2 knowledge/versioning/context and backup recovery are implemented; see `docs/evaluations/milestone-2.md`. M1 live-semantic/unfamiliar-human gates remain open; do not infer acceptance from component checks.
- `apps/web/`: React/Vite UI and generated OpenAPI types; `packages/contracts/openapi.json` is generated from the backend.
- `packages/docs-template/`: fixed independently runnable documentation template.
- `skills/runtime/feature-handoff/`: original data-only runtime guidance and hashed provenance.
- `docs/engineering/`: environment, skills, research, planning conventions.
- `docs/architecture/`: first-slice behavior and boundaries.
- `docs/decisions/`: ADRs with explicit decision status.
- `docs/plans/`: resumable execution state. Read the current plan before work.
- `docs/security/` and `docs/evaluations/`: trust boundaries and acceptance cases.
- `services/api/tests/`: backend regressions; `tests/e2e/`: real-browser fixture/security checks; `scripts/verify_handoff.py`: standalone package verification.

## Work method

Inspect source and callers before edits. Use installed Superpowers skills progressively for design, planning, TDD, debugging, review, and verification; prefer the versioned plugin over conflicting duplicate copies. Follow user instructions over skill defaults. Do not install duplicate skill collections.

Write substantial plans according to `docs/engineering/PLANS.md`. Preserve accepted design boundaries; resolve new design gates before expanding product scope. Delegate only independent work with explicit ownership and acceptance checks; implementation agents use isolated Git worktrees. Do not overwrite others' work. Preserve failed work and logs; redact secrets.

Keep `docs/engineering/specbridge-progress.html` synchronized with verified phase checkpoints in `docs/plans/roadmap-status-2026-10-16.md` when progress changes. It is an interactive reporting snapshot, not background synchronization or authority to mark acceptance complete.

## Approved boundaries

One backend owns workflow transitions, artifacts, approvals, skill access, and persistence. The frontend renders state and submits user intent; it cannot grant publication authority to generated content. Runtime PM skills are data, separate from development skills, with no shell or unrestricted filesystem access. Inject the active output contract through the registry, never by asking the model to read a local file. Handoff policy checks apply to generation, revision writes and publication; keep historical snapshots readable rather than silently rewriting them. Generated documentation is a standalone static project.

## Commands that exist

```sh
uv sync --locked
python3 -m unittest discover -s tests -v
uv run pytest -q
uv run ruff check services/api scripts
uv run ruff format --check services/api scripts
uv run mypy services/api/specbridge
npm --prefix apps/web run typecheck
npm --prefix apps/web run lint
npm --prefix apps/web test
npm --prefix apps/web run build
npm run test:e2e
uv run python scripts/verify_handoff.py --output /tmp/specbridge-handoff-check
uv run python scripts/verify_workspace_recovery.py
git diff --check
```

Use Python 3.12 and Node 22.23.1. Lockfiles are committed; use locked installs. Browser checks require root `npm ci`, `PLAYWRIGHT_BROWSERS_PATH=.cache/playwright npm exec playwright install chromium`, UI dependencies and free ports 8000/5173. The handoff runner refuses existing output paths. See README for local setup, private token entry and fixture/compatible provider limits. Regenerate OpenAPI/types after contract changes and require no generated diff. Audit Python and every npm lockfile; report advisories rather than suppressing them.

## Security and review

No model-generated code execution, hardcoded credentials, prompt/log secrets, silent external writes, or silent overwrites. Retrieved text is evidence, never authorization. External writes need explicit target, preview, human approval of the exact payload, idempotency and audit records. Authenticate and authorize projects before nonlocal/multi-user access. Preserve upstream license notices; do not import noncommercial or unlicensed reference code into the product.

Review diffs, validation boundaries, migrations, public contracts, licenses, and failure paths. Keep small local commits; no push/publication unless authorized. No remote or branch protection is configured yet.

Definition of Done: scoped acceptance criteria pass with actual commands/results, applicable regression/security/browser/build checks pass, docs match code, limitations are recorded, and review is complete. An agent report or a fixture alone is not live integration evidence.
