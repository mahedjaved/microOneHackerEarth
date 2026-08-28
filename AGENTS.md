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
