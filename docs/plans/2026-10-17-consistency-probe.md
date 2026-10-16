# Declared decision consistency: offline design probe

Status: verified for the offline diagnostic; production adoption not justified by these results. The continuing autonomous engineering instruction authorizes this bounded diagnostic, not new paid calls or a production schema migration.

Outcome: determine which known handoff failures explicit criterion/decision links can actually reject before introducing a larger generation contract. Source inspection: models.py stores criteria/questions as strings; validate_handoff checks story coverage/excerpts, not semantics; providers.py derives generation schema directly from Artifact. Active skill 1.2.0 already receives its output contract. Earlier 1.3.x checklist experiments failed and remain archived.

Options: more prompt rules (previously unsuccessful); production decision graph (costly, unproven); offline sidecar probe (chosen). Keep existing requirements as behavior units. A diagnostic sidecar maps criterion coordinates to requirement IDs and guarded unresolved decision options, and decisions to question indices. It binds artifact and source digests, makes no human selections and has no approval authority. Coordinates are only for frozen diagnostics, not a production ID design.

Lead owns scripts/probe_consistency.py, services/api/tests/test_consistency_probe.py and evidence/docs. A read-only architecture explorer reviewed source and proposed guarantees/blind spots; no concurrent implementation or worktree is needed. Use installed versioned Superpowers bounded design, TDD and verification. The probe is evaluation tooling only; no runtime import, migration, dependency, active skill or provider change.

Acceptance:

- [x] Twenty new tests failed before probe implementation, then passed; invalid references, uncovered requirements, missing/invalid guards and stale content are rejected.
- [x] Unmodified saved notification/deletion/API failures can have valid declared graphs while remaining semantic failures. Omitted dependencies and dishonest semantic mappings remain executable blind spots rather than fabricated rejections.
- [x] Hash original synthetic artifacts and acceptance pack; preserve them unchanged. Clean scoped Git diff confirms original evidence, production code and active skill unchanged. No credentials, network calls, model reasoning or real project data.
- [x] Combined backend/static checks passed and independent read-only review found no material issue. Do not promote: extra structure does not address all three motivating failures. [Results, guarantees and limits](../evaluations/decision-consistency-probe.md).

Reproduce with the existing locked environment: `.venv/bin/python -m pytest -q services/api/tests/test_consistency_probe.py`; `PYTHONPATH=services/api .venv/bin/python scripts/probe_consistency.py` emits a bounded JSON diagnostic from preserved synthetic trials. Full backend/static checks follow AGENTS.md. Next implementation depends on the observed guarantee/blind-spot matrix. M1 semantic and unfamiliar-human acceptance remain open.

Actual combined checks: 173 tests and 183 bootstrap subtests passed; Ruff lint/format passed (27 files), mypy passed (10 application sources), diff check passed. Three frozen semantic failures remain graph-valid; no original artifact or score changed. Next: define a concrete generation experiment with its exact preview/call scope, and run unfamiliar-engineer handoff acceptance separately. No production migration or additional live trial follows automatically from this probe.
