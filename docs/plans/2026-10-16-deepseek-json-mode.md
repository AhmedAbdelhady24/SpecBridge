# DeepSeek JSON-output configuration

Scope: user selected DeepSeek and supplied its key locally. Implement the bounded existing-adapter change needed to use that configuration. Do not disclose the key or make live calls. The hosted qualification proposal remains broader future work; this task does not implement Claude, usage metering or semantic evaluation.

Reach: `providers.py`, provider tests, `.env.example`, private `.env` settings (preserve credentials), README and execution evidence. Protocol stays `generate -> Artifact`; no public API schema change. Strict schema remains the default for existing callers.

- [x] Test explicit JSON-object request mode: schema/instructions in prompt, no strict-schema response_format, correct chat endpoint, full local output/citation validation, no retry/fallback.
- [x] Test configurable positive bounded output-token caps, invalid configuration, and incomplete finish reasons. Watch new cases fail first.
- [x] Implement minimum adapter branches and environment selection, configure local DeepSeek output mode, preserve secret bytes and 0600 permissions.
- [x] Run full backend/lint/typing and browser regression checks; inspect diff, document actual results and remaining live qualification. No paid call is authorized by this plan.

Success: mocked DeepSeek-style JSON responses pass the same Artifact/source validators; malformed, truncated, foreign-source and self-verified output fails; strict-mode callers remain compatible. Request token cap limits generated output but is not a dollar budget or proof that disconnected remote work stops.

Verified implementation: 116 backend tests plus bootstrap subtests; Ruff/mypy and 9 browser cases green. [Actual results and live-check limits](../evaluations/deepseek-adapter-readiness.md). One explicitly approved live attempt returned HTTP 200 but hit 4096 output tokens and was rejected as incomplete; no retry. Optional reasoning_effort configuration is now mock-tested with `none` in local settings. A second same-cap request preview awaits separate approval.
