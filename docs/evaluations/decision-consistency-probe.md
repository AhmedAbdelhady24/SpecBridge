# Decision consistency: structural links do not establish semantic quality

The offline probe does **not justify a production decision graph** as the next quality fix. All three preserved semantic failures can carry valid criterion/requirement/decision declarations. Extra structure would enforce declared references, but would not establish that a criterion measures the requested behavior or that all missing decisions were discovered.

## Source findings and alternatives

`services/api/specbridge/models.py` stores criteria and questions as strings; `validate_handoff` checks source/excerpt policy and story-level requirement coverage. `providers.py` derives generation schema directly from Artifact. `skills.py` already injects the active output contract correctly. This is not missing prompt injection plumbing. Earlier additive-checklist experiments failed and were archived; no new checklist was promoted here.

Considered more prompt rules, a production decision graph, and a small offline representability/falsification probe. Chose the probe to test the claimed benefit before paying migration costs. Existing requirements serve as behavior units; a second Behavior model would duplicate them.

The diagnostic schema exists only in `scripts/probe_consistency.py`. It binds an immutable Artifact and selected source text digests, maps criterion coordinates to existing requirements, and maps unresolved decisions to existing questions and named alternatives. Declared dependencies require matching guards. It neither chooses an alternative nor grants approval. Coordinates are acceptable for frozen samples; production editing would require stable identifiers and deliberate revision semantics.

## Observed guarantees and blind spots

| Condition | Probe result | Meaning |
| --- | --- | --- |
| Stale artifact/source text, duplicate/missing criterion, absent requirement/question/decision/option | Rejected | Declared references and content binding can be checked deterministically. |
| A declared dependency lacks a matching guard | Rejected | A known declared decision cannot silently lose its guard. |
| Declared requirement lacks criterion coverage | Rejected | Criterion-level declared coverage is stronger than the current story-level links. |
| Digest preference criteria test stored state rather than delivery | Graph accepted; original semantic fail retained | A link does not establish that the criterion tests the requirement. |
| Deletion draft omits timing/boundary/post-window questions | Graph accepted; original semantic fail retained | An omitted decision is invisible to a validator of declarations. |
| API draft has a circular page-transition criterion and missing mechanics/applicability questions | Graph accepted; original semantic fail retained | Incorrect semantic mappings and undeclared prerequisites remain possible. |
| A declared alternative is switched while criterion prose stays unchanged | Graph accepted | A valid option reference does not prove that prose matches its guard. |

The deliberately dishonest diagnostic baseline copies every story's requirement links to each of its criteria and omits all dependencies. It is an adversarial negative control, not annotation, a proposed prompt, or a corrected draft. No artifact or frozen criterion was edited. [Actual report and evidence fingerprints](decision-consistency-probe.json) retain the original three failing results. Fingerprints identify current input bytes; a separate clean Git diff against HEAD verified that preserved evidence, runtime code and active skill were unchanged.

## Verification and review

Twenty new tests failed before the missing probe was implemented, then passed. They exercise valid declarations, 15 malformed/stale declaration variants, the three saved semantic counterexamples, and report boundaries. The option-switch test intentionally accepts both alternatives structurally to demonstrate the blind spot. Independent read-only source review found no material issues; it did not execute tests.

Final combined verification: 173 backend tests and 183 bootstrap subtests passed in 1.30 seconds. Ruff lint passed; all 27 Python files passed formatting; mypy passed for 10 application sources; `git diff --check` passed. The diagnostic command completed successfully with three graph-valid/semantic-failed counterexamples and zero network calls. No original evaluation result was regraded.

Reproduce without credentials or network:

```sh
.venv/bin/python -m pytest -q services/api/tests/test_consistency_probe.py
PYTHONPATH=services/api .venv/bin/python scripts/probe_consistency.py
```

Used installed versioned Superpowers design/TDD/verification and a bounded read-only architecture explorer. Lead owns the probe, tests, evidence and integration; no concurrent implementation writer or worktree was necessary. No new dependency, provider call, active skill change, public contract, migration, production import or publication occurred. Existing application browser/export checks were not repeated because their code and contracts did not change.

## Decision and next work

Do not promote this schema or count its passing checks as better generation. Production adoption would touch generation/parsing, canonical ID remapping, checkpoints/revisions, editor controls, exports and publication policy, while all three motivating semantic failures can survive the proposed structure. Explicit links may become useful later for decision navigation, but that is a separate product outcome.

Keep explicit human correction/review. Next generation work should compare an explicitly scoped alternative generation configuration or decomposition against the same frozen sources and semantic criteria, rather than expand the production schema first. Any paid experiment needs a concrete call scope; prior bounded rounds are consumed. An actual unfamiliar engineer must still perform the handoff exercise. No model qualification, human acceptance or milestone advancement is claimed.
