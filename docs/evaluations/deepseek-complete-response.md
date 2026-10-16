# DeepSeek complete-response measurement — 2026-10-16

One explicitly authorized request omitted the client output-token parameter, used `reasoning_effort=none` and retained the 60-second HTTP deadline/256KiB response bound. DeepSeek's server defaults still applied. No retries occurred. This was the second live call overall; the earlier 4096-token attempt is retained separately.

## Actual result

- Requested endpoint/model: `https://api.deepseek.com`, `deepseek-flash`.
- HTTP 200; `finish_reason=stop`; completed in 7.76 seconds.
- Reported usage: 1446 prompt tokens + 1469 completion tokens = 2915 total.
- Full Artifact/source validation passed: 5 requirements, 2 stories, 8 open questions.
- [Complete generated draft](deepseek-complete-csv-draft.json) and [sanitized measurement](deepseek-complete-smoke-2026-10-16.json) are committed for review. The original full API response envelope remains locally in ignored `.cache/deepseek-complete-response.json`; provider request IDs/timestamps are not published in the sanitized evidence. The real credential was checked absent from the saved response and never printed.

## Selected limit

Set the DeepSeek `.env` and `.env.example` output limit to **3072 tokens**: twice 1469, rounded up to the next 1024-token boundary. Thinking remains disabled. The generic compatible-provider fallback default remains 4096; the explicit DeepSeek settings override it. The temporary omission existed only in the measurement call, not as an unbounded production option.

Loaded actual environment configuration and replayed the saved complete response through MockTransport: the constructed request sends `max_tokens=3072`, `reasoning_effort=none` and passes the same validators. No third live call was made. This replay verifies configuration and parsing; it does not prove that a future generation will use the same number of tokens.

The limit is calibrated to one small synthetic feature. Longer briefs, more stories or different models may require a higher explicitly configured cap. Do not call it a universal safe limit or infer a hard dollar budget. Actual cost was not calculated. Both thinking mode and client-cap omission changed between the two trials, so these observations do not isolate the cause of the first truncation.

## Draft review limits

Structural validity does not make this approved engineering scope. The model retained owner/date/size/permission unknowns, but inspection found review gaps:

- `STORY-1` describes using data in external tools and labels the whole statement user-provided; the source did not state that motivation. Review the evidence classification.
- `REQ-2` (headers) appears in acceptance criteria but has no explicit story-to-requirement ID link. Existing validators reject dangling links but do not guarantee every requirement is covered by a story link.
- Size/permission requirements are labeled unknown but use “shall”; a human must settle those decisions before treating them as implementation commitments.

This is agent inspection of one draft, not an unfamiliar engineer's acceptance exercise or a human-reviewed quality benchmark. No artifact approval, external publication, Jira write or documentation overwrite occurred. Next task: fix/measure traceability and evidence-label quality against curated references before full Milestone 1 acceptance.
