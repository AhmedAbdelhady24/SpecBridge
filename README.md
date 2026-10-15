# SpecBridge

SpecBridge will turn product information into traceable requirements, reviewed backlog proposals, and independently runnable engineering documentation.

**Current status: Phase Zero research and bootstrap. There is no application yet.** Architecture is proposed, not approved. No LLM, integration, or documentation website has been run. No external repository has been created or published.

Start with the [environment audit](docs/engineering/environment-audit.md), [skill inventory](docs/engineering/skill-inventory.md), [repository comparison](docs/engineering/reference-research.md), and [proposed architecture](docs/decisions/0001-local-modular-monolith.md).

The [bootstrap report](docs/engineering/bootstrap-report.md) records delivered files, skills, delegated reviews, actual checks and remaining gates.

The [first-slice design](docs/architecture/first-slice.md) defines the behavior to approve. The [execution roadmap](docs/plans/bootstrap-and-first-slice.md) records remaining gates and work packages. [PLANS.md](docs/engineering/PLANS.md) defines how future plans are maintained.

Run the bootstrap checks from the repository root, without installing dependencies:

```sh
python3 -m unittest discover -s tests -v
git diff --check
```

These checks validate documentation links and research inventory consistency. They do not prove product functionality, dependency compatibility, or hosted CI execution. Future backend, frontend, and documentation build commands will be added only when those components exist.

See [acceptance scenarios](docs/evaluations/acceptance.md) and [security boundaries](docs/security/threat-model.md) before implementation. Original SpecBridge code has no distribution license selected yet; do not interpret reference repository licenses as licensing this project.
