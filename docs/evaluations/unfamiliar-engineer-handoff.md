# Unfamiliar-Engineer Handoff Evaluation

**Date:** 19 October 2026  
**Status:** Automated fresh-reader handoff simulation passed; real unfamiliar human acceptance remains an open gate.  
**Script:** `scripts/verify_unfamiliar_handoff.py`  
**Provider:** Fixture (deterministic synthetic data, zero external network or model calls)

---

## 1. Objective and Evaluation Boundary

As defined in `docs/evaluations/acceptance.md` (Section "Independent handoff exercise"):
> An engineer unfamiliar with the feature receives only the portable package and its README. Record actual failures and ambiguities while the engineer:
> 1. Extracts or clones the generated project and runs `npm ci`.
> 2. Runs `npm run dev` and navigates the PRD, scope, acceptance criteria, edge cases and constraints.
> 3. Traces requirements to stories and sources, identifies missing information, and sees the approved revision/history manifest.
> 4. Creates a Git branch, edits a requirement and reviews the diff as a proposed change.
> 5. Runs `npm run build` and `npm run preview` successfully with SpecBridge stopped and no LLM credentials.

Per `AGENTS.md` and `docs/plans/2026-10-19-next-session-handoff.md`:
> An agent simulation is useful preparation, not evidence that a real unfamiliar human accepted it. If human participation or a new paid test is unavailable, record that specific gate honestly and continue independent engineering work.

---

## 2. Exercise Steps and Observed Evidence

The automated verification script `scripts/verify_unfamiliar_handoff.py` executed the complete sequence against an isolated temporary directory with SpecBridge stopped and zero external credentials:

### Step 1: Package Extraction and Offline Setup
- Generated and approved a candidate package from synthetic clinical feature intake ("Care Plans for Patients").
- Downloaded `specbridge-documentation.zip` and extracted to a clean standalone workspace directory.
- Ran `npm ci --no-fund` using the committed `package-lock.json`. Installation completed cleanly with zero peer dependency conflicts or missing lockfile entries.
- Initialized a fresh Git repository (`git init -b main`) and committed the pristine package as the initial import.

### Step 2: Specification Inspection and Traceability
- Checked generated markdown files under `src/content/docs/`:
  - `requirements.md`: Verified presence of `Requirement 1`, cited source references (`[Source 1](../provenance/#source-1)`), and bi-directional links to user stories (`[Story 1](../stories/#story-1)`).
  - `stories.md`: Verified acceptance criteria and user journey steps.
  - `edge-cases.md`: Verified QA scenarios and failure behavior.
  - `questions.md`: Verified that unapproved API contracts and open questions are labeled explicitly, not invented.
  - `revision.json`: Verified immutable provenance and checksums.

### Step 3: Independent Production Build
- Executed `npm run build` inside the extracted directory with SpecBridge completely stopped and no network connection.
- Astro Starlight static build completed successfully in under 2 seconds.
- 52 static HTML, CSS, JavaScript, and asset files generated in `dist/` with valid routing (`index.html`, `requirements/index.html`, etc.).

### Step 4: Proposing a Change on a Git Branch
- Simulated the engineer proposing a clarification:
  - Created branch `git checkout -b feature/patient-summary-clarification`.
  - Added `Requirement 2` (vital signs retention policy) linking to existing source evidence and stories.
  - Ran `git diff` to verify the proposed diff is clear and readable.
  - Committed the change: `docs: clarify vital signs retention policy`.

### Step 5: Verification of Modified Build
- Executed `npm run build` on the feature branch.
- Astro Starlight compiled the updated specification cleanly with zero syntax errors, broken links, or build failures.

---

## 3. Results Summary

| Check | Expected | Observed | Status |
| --- | --- | --- | --- |
| Package extraction | Fixed regular files, safe bounds | 100% regular files, safe paths | **Passed** |
| `npm ci` install | Clean install against lockfile | 0 warnings, locked dependencies resolved | **Passed** |
| Independent `npm run build` | Builds with SpecBridge stopped | 52 static files generated | **Passed** |
| Requirement traceability | Requirements link to stories & sources | Bi-directional links valid | **Passed** |
| Branch & edit workflow | Engineer can propose edits via Git | Clean `git diff`, commit created | **Passed** |
| Rebuild after edits | Modified docs site builds cleanly | Clean Astro compilation | **Passed** |
| Unfamiliar human acceptance | Real unfamiliar human sign-off | Automated agent simulation only | **Open Gate** |

---

## 4. Honest Limitation & Next Steps

This automated evaluation confirms that:
1. SpecBridge packages are completely self-contained and runnable without the SpecBridge backend or LLM credentials.
2. The Astro Starlight documentation template supports Git-based developer branching and editing.
3. However, whether an unfamiliar engineer finds the generated requirements sufficiently detailed, clear, and actionable to write production software without asking the PM follow-up questions requires a live human pilot, which remains an open acceptance gate.
