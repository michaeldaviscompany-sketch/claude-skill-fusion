---
name: agent-orchestration
description: Coordinate multiple AI agents so they do not corrupt each other's work or ship unverified output. Use whenever: agents run in parallel and files must be divided so they cannot overwrite each other; two agents edited the same file; an agent reports it finished and you must decide whether to trust, review, or merge its work; you want a quality gate before an expensive downstream stage (a long render, build, or deploy); an agent died, timed out, or hit a session limit and the work must resume across sessions; requirements changed while an agent is mid-task; or you are choosing which model tier runs which stage of a pipeline. Prefer this skill over code-review, model/API, or memory skills whenever the subject is an AGENT's output or an AGENT's lifecycle rather than your own code. Platform-agnostic. Do NOT use for editing a config file's contents, model pricing, CI/CD YAML, container orchestration, or single-shot tasks with no delegation.
license: PolyForm-Noncommercial-1.0.0
---

# Agent Orchestration

Running agents is easy. Getting *correct, premium work* out of a swarm of them is a coordination discipline. These practices come from a real multi-week-equivalent product build (CAD, renders, research, website) run through dozens of agent dispatches — every rule below was paid for by a concrete failure or near-miss.

Nothing here is specific to one agent platform. Wherever this says *dispatch a sub-agent*, read it as whatever your tooling calls delegating a scoped task to a fresh context — sub-agent, worker, background task, or a second terminal. The *coordinator* is whoever holds the plan: an orchestrating agent, or you.

The one-sentence version: **agents are optimistic reporters of their own work; the coordinator's job is to scope them so they can't collide, gate them so mediocrity can't propagate, and verify what they made — not what they said.**

## Scope agents to disjoint territory

Two agents writing the same file is corruption you'll discover much later. Before dispatching agents in parallel, partition the file tree:

- Give each agent an explicit list of what it owns and — just as important — an explicit **"do NOT touch"** list naming the other agent's territory.
- If agent B needs what agent A produces, don't share the directory — **sequence them**, or have A finish its outputs before B starts reading.
- When a file genuinely must change while another agent reads it, don't overwrite in place. Leave a flag file (`REEXPORT_NEEDED.md`) describing what must regenerate, and let the owner regenerate when the reader is done. Silent partial writes are miserable to debug.

Real failure this prevents: an engineering agent updating dimension constants while a render agent read the exports built from them — resolved by giving the engineer everything *except* the export directory, plus a flag file.

## Gate quality between stages — and review the artifact yourself

A pipeline is only as good as its worst unreviewed stage. Insert an explicit **quality gate** between stages: the downstream (expensive) stage does not start until the coordinator has inspected the upstream output.

The critical discipline at the gate: **the report is not the artifact.** Agents summarize their own work optimistically — not dishonestly, but they grade their intent, not their output. Open the files. Look at the renders. Measure the meshes. Run the page.

Real failures caught only by direct inspection, each *after* the agent reported success:
- An agent reported "credible store-display mannequin with defined shoulders"; the actual render showed stump arms and no hands. Two iterations of claimed fixes; the renders contradicted both.
- A model contained **three overlapping copies** of a 677k-vertex body (a dependency silently dragged in by an append); the agent's manifest said one.
- A measurement report gave a "male" connector whose tip circle was smaller than the bore it entered — self-contradictory numbers, flagged only because the coordinator sanity-checked them against each other.

Cheap gate checks that catch most of this: render or screenshot the output and *look at it*; count objects/components; cross-check two numbers that must be consistent; run the thing once. Have the producing agent deliver small check artifacts (low-res renders, manifests, dimension dumps) as part of its brief so the gate is fast.

The gate also protects budget: when a design direction changed mid-build, the coordinator rescoped the running render agent to "pipeline + material tests only" *before* it burned hours producing sequences of geometry that was about to be replaced. Gates are where you cancel wasted work early.

## Match model strength to task criticality

Not every task deserves the strongest model available, and quality-critical work shouldn't run on the cheapest one. Think in tiers rather than product names — the names change, the tiers don't:

- **Strongest tier**: precision geometry, design-taste work, anything where errors compound downstream, final-quality review.
- **Mid tier**: research sweeps, downloads, boilerplate, link checking, content plumbing.
- **The coordinator** does planning, briefs, gates, verification, and user communication — the judgment layer is the one thing not to delegate.

If the user corrects a model choice once ("use the better model for building"), treat it as a standing rule, not a one-off.

## Write briefs like contracts

Agents start cold. A good dispatch brief contains: the goal and the *quality bar* in plain words; file ownership (own / read-only / forbidden); the exact deliverables and paths; environment facts it can't discover cheaply (ports, licenses, installed tools, venv quirks); relevant hard-won context ("previous agent's partial work may exist — audit and supersede"); and what to do at the end (report format, what to verify before claiming done).

Two patterns worth the extra sentences:
- **Pre-authorize the fallback.** "If X fails, Y is pre-approved — don't agonize, commit and note the decision." Saves a full round-trip when the primary path dies.
- **Time-box exploration.** "Probe for ≤30 min, then commit to the fastest reliable path." Agents will happily explore forever.

## Steer running agents; don't restart them

A running agent with context is an asset. When requirements change mid-flight, send it a message (design changed, rescope to X; here's the correction) rather than killing and respawning — restarts pay the cold-start cost again and lose accumulated context. Queue direction changes as they arrive; agents pick them up at their next tool round.

But **do** stop an agent promptly when its remaining work is about to be invalidated (wrong geometry, wrong model tier, wrong direction) — the sunk cost of its progress is not a reason to let it finish producing outputs you'll discard.

## Design for agent death

Agents die: session limits, timeouts, process exits. Sometimes the transcript is unrecoverable. The recovery discipline:

- **State lives on disk, not in transcripts.** Require agents to write their work products and running notes (NOTES.md, manifests) as they go, so a successor can resume from files alone.
- On death, first **audit the disk** — the work may be more complete than the last message suggested (an agent that died "mid-task" had in fact finished everything but the final report).
- When respawning, brief the successor that partial work exists and may be half-applied: "audit first, then complete; your results supersede."

## Keep the coordinator lean

The coordinator's context is the scarcest resource in the system. Don't read delegated agents' transcripts (they're enormous); read their *deliverables*. Don't re-derive what an agent already established; trust the gate you ran. Peek at output directories and file timestamps for progress checks instead of interrogating the agent. Between dispatches, record decisions in small durable files (memory notes, decision logs) rather than carrying them in-context.

## Stage contracts decouple the pipeline

When one stage produces assets another consumes, fix the **contract** first: exact paths, naming (zero-padded frames, poster files), formats, orientation/units conventions. Then both sides build independently — the consumer against watermarked placeholders, the producer to the contract — and integration is a file drop with zero code changes. Document the contract in a file both agents are pointed at; it is an interface between programs, and it deserves the same rigor.

## Research before building; steelman before committing

For any direction-setting decision (a product pivot, a claim, a costly build), dispatch a research agent with an explicitly two-sided brief: *steelman the hypothesis, then stress-test it, cite everything, and state what would make us walk away.* Instruct it not to tell the requester what they want to hear — decision-grade research that kills a bad idea in an afternoon is the highest-ROI dispatch there is. Gate big builds behind the memo.

## Operating modes: surgical vs boil-the-ocean

Most requests deserve the smallest dispatch that answers the question. But when the user asks for *everything* — "do everything properly, boil the ocean" — switch modes deliberately rather than just working harder:

- **Stand up the whole pipeline at once.** Map every stage to completion (research → engineering → assets → delivery), dispatch the independent stages in parallel immediately, and chain the dependent ones on completion notifications instead of waiting to be asked.
- **Gates matter *more*, not less.** Maximal throughput without inspection is how you ship maximal slop. Every stage still stops at a coordinator review before the next expensive stage fires.
- **Pre-build the contracts** (file territories, asset paths, naming) for all stages up front, since you won't have the luxury of designing them one at a time.
- **Keep a cancellation trigger in mind for each running stage** — in a many-agent pipeline, the coordinator's highest-value action is usually stopping something whose premise just changed.
- **Report by exception.** With many streams running, the user needs the deltas and the decisions, not a log.

Boil-the-ocean is a commitment to *completeness with gates*, not to speed without them.

## Dispatch checklist

Before spawning: single owner per file territory? quality bar stated? fallbacks pre-authorized? deliverables + check artifacts specified? right model for criticality?
At the gate: opened the actual artifacts? cross-checked numbers that must agree? counted what should be counted? cheap check-renders before expensive finals?
On death: disk audited before respawn? successor told to audit-and-supersede?

## License

Free for individuals and noncommercial use under PolyForm Noncommercial 1.0.0.
Commercial use requires a paid license — see the repository's `LICENSE.md` and `COMMERCIAL.md`.
