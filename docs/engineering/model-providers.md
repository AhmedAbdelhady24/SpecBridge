# Model providers and local serving

Run commands from the repository root with the locked environment. The application defaults to the deterministic fixture provider; it does not load `.env` automatically.

## Fixture mode

```sh
SPECBRIDGE_PROVIDER=fixture PYTHONPATH=services/api uv run python -m specbridge
```

Fixture mode makes no model/network call and emits generic DEMO artifacts. It verifies the workflow, not understanding of arbitrary feature requests.

## Configure an OpenAI-compatible endpoint

Create `.env` only if it does not already exist:

```sh
cp -n .env.example .env
```

Edit the private file locally. The example targets DeepSeek with JSON-object output; add the key there, not in chat or a committed file. Preserve an existing `.env` and its owner-only permissions. Start explicitly:

```sh
PYTHONPATH=services/api uv run --env-file .env python -m specbridge
```

Restart the API after changing settings. Inspect the destination displayed in the UI before acknowledging generation. Selected evidence is sent to that endpoint and hosted use may incur charges. The browser never receives the provider key.

| Variable | Behavior |
| --- | --- |
| `SPECBRIDGE_PROVIDER` | `fixture` by default; `compatible` opts into API generation |
| `SPECBRIDGE_LLM_BASE_URL` | Explicit base URL; HTTPS, or HTTP for a loopback endpoint |
| `SPECBRIDGE_LLM_MODEL` | Provider-supported model identifier |
| `SPECBRIDGE_LLM_API_KEY` | Private process credential, sent in the authorization header |
| `SPECBRIDGE_LLM_OUTPUT_MODE` | `json_schema` by default; the DeepSeek example uses `json_object` |
| `SPECBRIDGE_LLM_MAX_TOKENS` | Application output cap, 1–16384; unset defaults to 4096, example 3072 |
| `SPECBRIDGE_LLM_REASONING_EFFORT` | Optional provider-supported value: `none`, `low`, `medium`, or `high`; omitted when unset |
| `SPECBRIDGE_LLM_TIMEOUT_SECONDS` | Unset defaults to 60 seconds; finite positive seconds set a whole-request deadline; `none` explicitly disables generation deadlines |

Both output modes enforce the same local Artifact/source rules. User-provided claims must be exact source excerpts, every requirement needs a story link, unknown constraints stay questions, and generated text cannot self-verify. Schema validity alone does not prove semantic correctness. See [handoff rules](../evaluations/handoff-rules-results.md).

The transport disables redirects and ambient proxy credentials, limits response size, and makes no automatic retry. Truncated responses fail. Configured credentials found in a payload or generated artifact are rejected rather than redacted. Use a distinct synthetic credential for mock/local configurations; a common placeholder matching a model name or prompt text can trigger this guard. It does not detect arbitrary unknown secrets.

## Long-running requests

`SPECBRIDGE_LLM_TIMEOUT_SECONDS=none` removes generation total/read deadlines. Connection establishment remains bounded to at most 30 seconds, and response-size bounds remain. Waiting without a generation deadline does not guarantee completion, correctness, or a dollar budget.

The workflow renews its owned lease during generation. A stopped process stops renewal; recovery requires explicit retry acknowledgment. If renewal fails, the returned result is discarded. An already stalled provider call may continue until it returns or the process is stopped. See [long-generation verification](../evaluations/long-generation.md).

## Application versus evaluation settings

The environment example's Flash/non-thinking configuration is separate from the evaluation-only Pro/high typed-plan candidate. The candidate passed two recorded 5/5 rounds on the same frozen pack but is not wired into application generation. Diagnostic cap omission does not remove the application's configured token cap. Do not infer runtime promotion or broad reliability from a benchmark score.

See [candidate design and earlier failures](../evaluations/compiled-handoff.md), the [fresh repeat](../evaluations/post-audit-live-retest.md), and [current phase status](../plans/roadmap-status-2026-10-16.md). Native Claude and local-model serving remain unqualified; accepting a loopback URL is not live local-model evidence.

## Serve the built UI from the API

Build the UI, then restart the API with its matching origin:

```sh
npm --prefix apps/web run build
SPECBRIDGE_PROVIDER=fixture SPECBRIDGE_UI_ORIGIN=http://127.0.0.1:8000 PYTHONPATH=services/api uv run python -m specbridge
```

Open `http://127.0.0.1:8000`. For compatible generation, use the explicit environment-file launcher above with the same origin setting. Both modes bind to loopback. This does not configure public hosting or multi-user authentication.
