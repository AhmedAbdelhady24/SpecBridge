# Initial security boundaries

Status: design requirements; controls are not implemented yet.

| Threat | Required control | Verification before first-slice completion |
| --- | --- | --- |
| Prompt injection in notes/skills | Treat all content as data; runtime has no shell/external write tools | Malicious source cannot approve, execute code or change provider destination |
| Skill path traversal/symlink escape | Resolve references beneath configured root; reject escaped/symlink paths, oversized files and invalid metadata; YAML safe loader | Absolute, `..`, symlink, duplicate/invalid metadata and oversized fixture cases |
| Approval replay or race with edit | Immutable revision + preview digest binding template, paths, file/asset hashes checked in transaction; serve stored reviewed bytes | Old approval fails after content/template/asset change; concurrent approval/export cannot select different bytes |
| Local browser cross-origin request/DNS rebinding | Loopback binding, host/origin checks and local mutation authorization | Foreign Origin/Host and missing local session authorization rejected |
| Cross-project leakage | Project-scoped lookups, server-selected context | Source/artifact IDs from another project rejected |
| Provider data leakage / SSRF | Operator-configured destination, bounded requests, no destination selection from input; no redirect credential forwarding | Mock transport checks destination, secret redaction, timeouts and no redirects |
| Stored HTML/MDX/script injection in preview or export | Fixed audited template/frontmatter serialization; text escaping; safe URL policy; no remote assets or model config/scripts | Raw HTML, event attributes, remote Markdown images, unsafe URLs, frontmatter delimiters and MDX import/expression fixtures remain inert; build and browser tests |
| ZIP path traversal or overwrite | Fixed relative paths, bounded assets, fresh export directory, deterministic manifest | ZIP entry paths confined; existing authored files retained |
| Duplicate external write after retry | Preview-bound approval, idempotency key, audit and reconcile ambiguous failures | Mock integration replay produces one write; real adapters deferred |
| Secrets in source/logs/artifacts | Environment credentials; redact operational errors; no prompt/body logging by default | Sentinel secret absent from logs/exports/errors |
| Supply chain/licensing | Exact revisions, lockfiles, license inventory, audited scripts before execution | Dependency audit/build gates; no unlicensed/noncommercial runtime imports |

The local session control does not establish a multi-user identity. Add authentication, membership authorization, transport security, retention/deletion controls and deployment review before external or multi-user access. SQLite at-rest encryption is not promised; local data remains sensitive under OS account permissions.

Do not execute the reference calculator (`eval`), SDK permission bypasses, mutable `npx -y` MCP bootstrap, or model-selected file writers identified in the [source review](../engineering/reference-research.md).

The Anthropic MCP Builder evaluator sends data to Anthropic and invokes configured MCP tools; it has not been authorized or executed. A source review is not runtime safety certification.
