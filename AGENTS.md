# AGENTS.md — microOne HackerEarth

## What this repo is

This is an entry for the **micro1 Agentic Workflows Hackathon** (HackerEarth).
The challenge: pick a meaningful, well-understood problem and use AI agents to
solve it, demonstrating clear measurable improvement over a fair baseline.

The full challenge brief lives in `docs/micro1 - First Hackathon97ce7c5.pdf`.
**This file is gitignored** — see `.gitignore`. Do not move, rename, or delete
it. It is the project's source of truth and is not recoverable from git.

## Current phase

**Problem definition only. No code yet.** The repo currently contains only
`.git/`, `.gitignore`, and the gitignored `docs/` folder. The intended workflow
(before any implementation) is:

1. Define the problem in `docs/problem.docx` (or equivalent).
2. Adopt spec-driven development via **speckit**.
3. Draft a `constitution.md` capturing project principles and constraints.

Do not write application code until the problem and spec are in place.

## Shell and environment

- **OS:** Windows, **shell is PowerShell** (not bash). `ls`, `la` flags, and
  other bash-isms do not work. Use `Get-ChildItem`, `Select-Object`, etc.
- **Python:** available at system path (Python 3.10). `pypdf` is installed for
  reading the hackathon PDF if needed again.

## Hackathon structure you must satisfy

Judging is out of 100 pts across: Problem & User Value (15), Agent Solution &
Engineering (30), End-to-End Quality (20), Measured Improvement (15),
Reproducibility (15), Hot Take / Insights (5).

Required deliverables (per the brief):
- **Code + Improvement Changelog** — every meaningful iteration tied to evidence,
  including removed experiments and what they taught you.
- **Reproduction guide** — written for a clean environment; exact commands,
  data, expected output, versions, runtime, cost.
- **Solution video** (≤5 min) — problem, baseline, one full execution, final
  comparison, biggest contributing change, one removed experiment.
- **Agent trajectories** — representative runs per agent, from instructions
  through tools/responses to final result, including retries and human checkpoints.

## Ground rules (binding)

- Keep consequential actions in a sandbox/simulation; require human approval
  before real effects.
- Include a qualified human reviewer for anything that could significantly
  affect someone.
- Use only public, synthetic, or approved-anonymous data. No private data.
- **No credentials or private info in the submission.**
- Every claim about results must link to submitted evidence.
- Judges must be able to run and reproduce the main result.

## Repo conventions

- `/docs` and `/notes` are gitignored — reference material, drafts, and large
  files go there and are not tracked.
- `.kilo/`, `.claude/`, `.opencode/` are also gitignored.
- Keep the working tree clean; the submission must be reproducible from clone.

## Speckit (spec-driven development)

This project uses [speckit](https://github.com/github/spec-kit) for spec-driven development.
The CLI is installed in `.venv` (Python 3.11). All speckit commands must run via the venv:

```powershell
.venv\Scripts\specify.exe <command>
```

Available commands (also registered as Kilo slash commands in `.kilo/commands/`):
- `/speckit.constitution` — establish/update project principles (`.specify/memory/constitution.md`)
- `/speckit.specify` — create baseline spec (who, bottleneck, why it matters)
- `/speckit.clarify` — resolve ambiguities before planning
- `/speckit.plan` — generate implementation plan
- `/speckit.checklist` — validate requirements completeness
- `/speckit.tasks` — break plan into actionable tasks
- `/speckit.analyze` — cross-artifact consistency check (run before implement)
- `/speckit.implement` — execute tasks
- `/speckit.converge` — assess codebase against artifacts, append remaining work

**Artifacts live in:**
- `.specify/memory/constitution.md` — project principles (currently a template, needs filling)
- `.specify/templates/` — spec, plan, tasks, checklist templates
- `.specify/scripts/powershell/` — helper scripts (PowerShell, since this is Windows)

**Workflow order:** constitution → specify → clarify → plan → checklist → tasks → analyze → implement → converge

**Rules:**
- Do not run speckit outside the `.venv` — the CLI is not globally installed.
- Always run from the repo root (`D:\PROJECTS\CLAUDE_CLI_AGENTS\HACKER_EARTH\HACKATHONS\microOneHackerEarth`).
- PowerShell scripts (`.ps1`) are the native script type here, not bash.

# Research Engineering Rules

## Correctness

Passing tests does not establish scientific correctness.

Plausible output does not establish scientific correctness.

Improved benchmark performance does not establish scientific correctness.

Significant changes require both engineering and scientific validation.

## Investigation

For unexpected behaviour:

1. Reproduce it.
2. Establish expected behaviour.
3. Trace the relevant code/data flow.
4. Form competing hypotheses.
5. Run discriminating experiments.
6. Establish root cause.
7. Implement the smallest justified fix.
8. Re-run validation.

Do not repeatedly change code until the symptom disappears.

## Scientific implementations

When implementing scientific methods:

- identify the mathematical formulation
- identify the implementation
- verify assumptions
- verify equations
- verify units
- verify dimensions
- verify numerical conventions
- verify preprocessing
- verify evaluation methodology
- verify experimental controls

Use primary literature/specifications when available.

## Supervisor

Use `research-supervisor` when:

- root cause is uncertain
- competing explanations exist
- scientific correctness is questionable
- numerical behaviour is unexpected
- core algorithms are changing
- experimental methodology is changing
- evidence is contradictory
- a significant conclusion is about to be made

The supervisor is an independent reviewer.

It should challenge conclusions rather than merely confirm them.

## Supervisor and reviewer (mandatory two-agent consultation)

For every non-trivial change to a scientifically or architecturally
significant component — and **especially** before declaring a
significant issue resolved — consult BOTH independent reviewers:

1. **`research-supervisor`** — for diagnosis, hypothesis evaluation,
   and scientific/engineering reasoning when the root cause is
   uncertain or the change touches a core scientific algorithm.

2. **`research-reviewer`** — for independent validation of the
   proposed fix and the evidence supporting it, after implementation
   and before declaring the issue resolved.

The two agents serve different purposes:

- The **supervisor** asks: "What is probably causing this?"
- The **reviewer** asks: "Is the proposed solution actually justified?"

Workflow:

```
Step 3.7 Flash (investigation)
        │
        ▼
   research-supervisor  ──► diagnosis / next experiment
        │
        ▼
Step 3.7 Flash (implements, tests)
        │
        ▼
   research-reviewer  ──► APPROVE / REJECT (before declaring resolved)
```

Do not declare a significant change complete based solely on
passing tests. The reviewer must independently confirm.

## Final conclusions

For significant changes report:

- root cause
- fix
- evidence
- tests
- scientific validity
- engineering validity
- remaining uncertainty
