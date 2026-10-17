# Proposed model crossover and accessible progress overview

Status: preview verified; paid execution awaits explicit approval of the new model. User requested continuing engineering and asked why the inline phase board was unavailable on their device. Do not reuse the consumed high-effort round or treat this proposal as authorization to call a new billed model.

## Accessible overview

Official [OpenAI visualization documentation](https://learn.chatgpt.com/docs/visualizations) says availability depends on plan/platform/account/workspace and app version. CLI/IDE extensions do not render the view; web is supported for eligible accounts and desktop/mobile rollout varies. No exact device diagnosis is asserted because the user has not identified their client. The HTML board's successful Chromium checks do not establish support in the chat client.

Exported the existing board to the ignored, local `exports/specbridge-progress.html` using the installed visualization exporter. Its three unused tooltip/icon CDN script tags were removed from the generated copy only. The source uses native details/summary and no icons/tooltips, so these libraries are unnecessary. Installed skill assets and the canonical board were unchanged. The first offline check identified the unused network requests; after removing them, seven cards, expansion/collapse and 736px/320px layouts passed with zero page errors and zero external requests. This is an ordinary local browser file, not a remotely accessible or published site. Copy it to another device to open it there. Phase status is unchanged: M0 locally delivered, M1 acceptance open, M2–M6 remaining.

## Next generation hypothesis

Low and high effort each passed 2/5 semantic cases, failed checklist versions are archived, and explicit graphs did not establish behavioral completeness. Compare a different model before adding a two-stage pipeline. A read-only advisor inspected the actual failures and recommended this smallest single-variable screen; if it fails, test decomposition separately rather than continue model shopping.

Current official [DeepSeek models/pricing](https://api-docs.deepseek.com/quick_start/pricing/) advertises deepseek-v4-pro, JSON output and thinking at the same endpoint. Fetched table lists Pro version V4-Pro-0813 and Flash version V4.1-Flash-1017. Earlier news about retiring/rerouting Pro conflicts with current pricing; use the current model table as the proposal basis, not the old retirement claim. Model quality/access is unverified. Provider alias/version drift and stochastic variation limit causal inference from a small comparison.

Concrete proposed payload: [exact five requests](../evaluations/pro-model-preview-2026-10-17/preview.json); [hashes and comparison](../evaluations/pro-model-preview-2026-10-17/comparison.json). Maximum five calls, one per original synthetic case, no retries/repair, same https://api.deepseek.com endpoint and existing local key. Change only requested model deepseek-flash→deepseek-v4-pro. Preserve skill1.2.0, original sources/order, schema, JSON-object output, high effort, omitted client output caps and 60s/256KiB safeguards. No real project data, prompt change, .env modification, runtime promotion, artifact approval or publication. Pro rates differ and actual cost is unknown; the uncapped request does not establish a dollar budget.

Approval digest `11154ee258d2e26a51f643cebea1d6962f9f218db63db57a77926fd5759a6341` is SHA256 of the runner's sorted compact canonical JSON, not the pretty file's bytes. The comparison record separately includes the byte hash. Before any approved execution, regenerate with private .env loaded, override only model/effort inside that process, and require the exact canonical digest above. Abort if baseline endpoint/model/output mode changed. Existing runner revalidates current preview binding, never overwrites an existing result directory, and makes one attempt per case.

Acceptance and ownership:

- [x] Lead prepared preview without .env or credentials, using an inert placeholder; preview captured before any network operation.
- [x] Exact recursive comparison proves only five request body.model values differ from the high baseline; active skill/source/evaluator unchanged.
- [x] Read-only advisor reviewed actual preview scope; canonical-vs-file digest ambiguity clarified explicitly.
- [ ] Obtain explicit approval for the new billed model and exact five-call scope before execution.
- [ ] If approved, retain all final outputs/rejections/usage; replay real backend policy and independently grade unchanged frozen criteria. No repairing or pooling samples across configurations.
- [ ] Stop after one round; no further model trial. Even 5/5 only qualifies a screening pack, not unseen cases, production reliability or unfamiliar-human handoff.

Root owns preview, export and documentation; advisor is read-only. No implementation worker or worktree is necessary because no application source changes are planned. Used installed OpenAI Docs, visualization export and Superpowers investigation/verification guidance. No new dependency or paid call made while preparing this proposal.

Final preparation checks: 173 tests and 195 bootstrap subtests passed in 1.28 seconds; Ruff lint/format passed (27 files); mypy passed (10 application sources); diff check passed. The final browser export check passed with all seven cards, expansion/collapse, 736px/320px layouts, zero page errors and zero external requests. [Readiness record](../evaluations/pro-model-preview-2026-10-17/readiness.json) includes artifact hashes. Exporter defaults initially requested optional tooltip/icon libraries; those requests were diagnosed and removed from the local generated copy, rather than hidden by a passing network filter. Canonical board and installed plugins remain unchanged.

The asynchronous client/platform clarification and the exact five-call Pro authorization were requested. Until an explicit approval arrives, do not execute the preview. Recorded hosted attempts remain 40. This preparation is complete; paid execution is a separate pending step, and no milestone has advanced.
