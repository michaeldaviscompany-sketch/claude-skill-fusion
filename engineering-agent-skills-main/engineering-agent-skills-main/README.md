# Engineering Agent Skills

Agent Skills for engineering real parts: concept, parametric CAD, verified exports,
photoreal renders, and the discipline to coordinate the agents doing the work.
Everything here came out of shipping things, not from a blog post.

**Free for individuals and noncommercial use.** Commercial use needs a paid license.
See [LICENSE.md](LICENSE.md) and [COMMERCIAL.md](COMMERCIAL.md) (PolyForm
Noncommercial 1.0.0, source-available).

## The skills

| Skill | What it does | Triggers when you're… |
|---|---|---|
| [`hardware-cad-pipeline`](hardware-cad-pipeline/) | Physical part from concept → dimensionally-correct parametric CAD → verified STEP/STL/GLB → photoreal renders. Tool selection (OpenSCAD / build123d / Fusion 360 MCP / Blender), dimension authority, tolerances & DFM, prototyping, artifact verification. Ships three tested scripts (mesh measurement, export verification, Fusion MCP probe). | modeling or dimensioning a part, producing STL/STEP/GLB, rendering a product, connecting to Fusion 360, writing OpenSCAD/build123d/CadQuery, preparing for 3D printing |
| [`agent-orchestration`](agent-orchestration/) | Coordinating multiple AI agents on one project without them corrupting each other's work or shipping unverified output: file-territory scoping, quality gates, verify-the-artifact-not-the-report, model selection by criticality, steering running agents, recovering from agent death. | spawning subagents, planning a multi-agent pipeline, reviewing a subagent's work, recovering a killed agent, staging any long task |

## Install

These follow the **open Agent Skills standard** (a `SKILL.md` plus optional
`references/`, `scripts/`, `assets/`), so they work unmodified in any agent that
supports it: opencode, Codex CLI, Claude Code, Cursor, Gemini CLI, Copilot,
Windsurf, Goose, and 40+ others. Nothing here is tied to one vendor.

**Any agent (recommended).** Installs to every AI tool you have at once:
```
npx skills add lukeoishi/engineering-agent-skills
```
Target a specific tool with `--agent opencode` (or `codex`, `claude-code`, …),
or list what's available first with `npx skills list lukeoishi/engineering-agent-skills`.

**Manual.** Copy a skill folder into wherever your agent looks for skills:

| Agent | Location |
|---|---|
| opencode | `.opencode/skill/` (project) or `~/.config/opencode/skill/` (global) |
| Codex CLI | `~/.codex/skills/` |
| Claude Code | `.claude/skills/` (project) or `~/.claude/skills/` (global) |
| others | see your agent's skills documentation |

## About

I'm Luke Oishi. I was ranked #1 in my state in STEM and I'm now studying Aeronautical
Engineering at Imperial College London, though the thing that shaped how I actually
work sits outside any of that. I got into agentic workflows early, and what struck me
straight away was that the obvious use, writing code faster, is the least interesting
one. The leverage is in engineering. Drive the agents properly and a part goes from a
measured reference to a verified STEP file to a photoreal render inside an afternoon.

Most people never get there. They ask one agent one question and believe the answer.
What I run instead is a pipeline: several agents working in parallel, each scoped to
files the others cannot touch, with a gate at every stage where I open the artifact
and check it myself. Agents are fast and confident, and they will hand you three
copies of the same mesh while reporting success. The discipline is knowing that, and
building for it.

I expect this to become the default way engineering is done, and the advantage
belongs to whoever masters it first.

## Notes

- These steer an agent. They do not guarantee an outcome. Check the output.
- The Fusion 360 MCP notes reflect Autodesk's 2026 behaviour and will drift.
- The CAD scripts need `python3` with `trimesh` and `numpy`.
- Commercial licensing is handled case by case: see [COMMERCIAL.md](COMMERCIAL.md).
