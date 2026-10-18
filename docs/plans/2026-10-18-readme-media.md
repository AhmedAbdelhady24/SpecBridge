# README media — 18 October 2026

Status: verified locally. User requested videos, screenshots and architecture using Playwright and Hyperframes. Existing autopilot authorization applies to this reversible local documentation work; no hosted generation, publication or private workspace capture is included.

## Outcome and acceptance

- Capture real intake, review, exact-package approval and exported Starlight screens using Playwright against an isolated fixture workspace.
- Produce a captioned 30-second Hyperframes MP4 and lightweight GIF preview using those captures, with clear DEMO labeling and no implied live-model/human acceptance.
- Add an architecture image showing current module and trust boundaries, plus accessible README links/captions.
- Keep reproducible capture/composition sources, pinned media-only tooling, dependency audit and actual verification results. No change to app dependencies, contracts or runtime.
- Check screenshot readability, video scene midpoints, durations, local links and relevant browser regressions. Preserve current M1 limitations.

## Sources, boundaries and execution

Inspected README, first-slice architecture, current roadmap, App.tsx, Playwright config/helpers/handoff tests and bootstrap checks. Codebase-memory skill read; graph tools unavailable, so structural claims use the actual bounded sources above. Read official Hyperframes core/CLI/product-launch guidance from heygen-com/hyperframes revision dc0e80e73af185cc892ea90d5a9f1412a055e9a1. Tooling: Hyperframes 0.8.171 (Apache-2.0), GSAP 3.15.0 (upstream standard no-charge license), installed with lifecycle scripts disabled. No third-party skills installed or assets vendored. Use original screenshots and SVG; no music/voice service. Telemetry disabled. User request authorizes local rendering, overriding upstream interactive preview gates. No external writes/cloud rendering.

Single lead owns README, docs/media, scripts/readme-media*, this plan. Work is sequential because captures feed composition. No implementation delegation needed.

## Execution

- [x] Create isolated Playwright capture with UI assertions and approved ZIP export.
- [x] Build/run exported website and capture its actual content.
- [x] Author current-state architecture and Hyperframes composition.
- [x] Validate/render/inspect final media and embed README.
- [x] Run relevant checks, inspect diff, record results and limitations.

Reproduce using instructions in scripts/readme-media/README.md once complete. Captures use fresh temp data, never .env or the owner's .data; rollback is the scoped documentation changeset. Private session tokens are not recorded; trace/video recording are disabled for the capture. Fixture approval only authorizes the synthetic local ZIP.

## Actual results and review

- Isolated Playwright capture: 1 passed in 8.2s, including approved ZIP download, locked install, Starlight build and real requirements page. Four 1440×1000 PNGs inspected; original architecture SVG inspected in the video.
- Hyperframes strict check: zero lint/runtime/layout/contrast errors or warnings at six scene midpoints; 32/32 sampled text contrast checks. Decoded all six MP4 scene midpoints and inspected them. No blank/missing scenes.
- MP4: H.264, 1440×1000, 24fps, 720 frames, exactly 30 seconds, 1,718,937 bytes. Local hardware/drawelement capture, 7.1s final render. GIF: 720×500, 8fps, 30seconds; 1.5MiB. No audio is intentional: captions carry the sequence.
- Existing browser suite: 19 passed in 15.9s. Backend module-runner comparison:317 passed / 272 subtests. Documented pytest entrypoint initially could not import the root scripts namespace; explicit repository-root pythonpath fixes that command. After the configuration fix, `uv run pytest -q` passed 317 tests and 272 subtests in 2.65s.
- Bootstrap links initially failed because assets were not rendered yet and recursive discovery included installed dependency READMEs. After rendering, scope discovery to maintained Markdown by excluding node_modules and private .hyperframes state; both bootstrap tests pass. No assertions were weakened for authored docs.
- Media npm install/audit:79packages, zero known vulnerabilities. Existing application lockfiles unchanged. Runtime/dependency code untouched. No third-party skills installed: upstream entry/core/CLI guidance was read progressively. Used Agent Reach for source inspection, codebase-memory source fallback and Superpowers debugging for test-runner diagnosis. No subagents needed for this dependent capture/render task.
- Rejected parent-relative assets were moved inside the composition root; six scene sub-compositions and stable Studio IDs clear all strict warnings. The failed attempts are recorded here rather than treated as passing verification.

Limitations: snapshots and video show fixture behavior, not AI semantic quality, human acceptance, or unimplemented integrations. Desktop/README clients vary in MP4 handling, so the README offers a GIF and static PNG/SVG views. Hyperframes usage lookup returned unknown; no hosted allowance was used. Hyperframes cached its default Inter font during compilation, so first-time builds are not claimed offline. No keys, owner workspace data, public hosting or paid LLM calls were used. Next product task remains runtime adoption of the qualified generation candidate and unfamiliar-engineer acceptance; this documentation work does not complete M1.

Final capture recovery: a repeat exposed Astro preview daemon reuse and an ESRCH shutdown error. The capture now starts the Astro binary with --ignore-lock on a fresh ephemeral port, verifies the exact generated requirement ID, and asserts that the preview is unreachable after cleanup. The verified orphan from the initial attempt was stopped. Two consecutive final captures passed (6.9s/6.6s; 15.0s total), including cleanup assertions. Fresh screenshots were used for the final render.

Frontend typecheck, lint, 2 unit tests and production build passed. Ruff check/format passed (39 Python files); mypy passed (11 sources). No model/provider changes were made. The only test infrastructure changes exclude vendor/render-state Markdown from authored-link validation and make the documented pytest entrypoint resolve root scripts consistently.

Final strict check: zero lint/runtime/layout warnings or errors across nine layout samples; 32/32 sampled text contrast checks pass. GIF regenerated from the final MP4. Both media durations verified by ffprobe at 30 seconds; all README section anchors resolve.
