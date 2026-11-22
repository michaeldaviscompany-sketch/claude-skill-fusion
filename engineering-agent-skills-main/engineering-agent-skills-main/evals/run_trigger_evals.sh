#!/usr/bin/env bash
# Optimize each skill's `description` for trigger accuracy.
#
# WHY: an agent only sees a skill's name + description at startup. If the
# description doesn't match how people actually phrase their problems, the skill
# never opens and everything inside it is dead weight. This loop measures the real
# trigger rate against a hand-written should/should-not-fire query set, proposes
# better descriptions, re-tests, and keeps the best by held-out score.
#
# MAINTAINER TOOL — not needed to USE these skills. The skills themselves are
# platform-agnostic (opencode, Codex, Claude Code, Cursor, ...). This particular
# tuning harness happens to be built on Anthropic's skill-creator, so it needs the
# `claude` CLI on PATH (npm i -g @anthropic-ai/claude-code), authenticated once in
# an interactive shell. The equivalent check for any other platform is the same
# idea: run the should/should-not-fire query set and see whether the skill opens.
#
# COST: ~(queries x 3 attempts x iterations) headless calls per skill.
# Sonnet keeps it cheap; --max-iterations 3 keeps it bounded.
#
# USAGE:  ./skills/evals/run_trigger_evals.sh [model]
set -euo pipefail

MODEL="${1:-claude-sonnet-5}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

SKILL_CREATOR="$(find "$HOME/Library/Application Support/Claude" \
  -type d -name skill-creator 2>/dev/null | head -1)"

if [[ -z "$SKILL_CREATOR" ]]; then
  echo "error: skill-creator not found. It ships with the anthropic-skills plugin." >&2
  exit 1
fi
if ! command -v claude >/dev/null 2>&1; then
  echo "error: the 'claude' CLI is not on PATH. Install with:" >&2
  echo "       npm i -g @anthropic-ai/claude-code" >&2
  exit 1
fi

for skill in hardware-cad-pipeline agent-orchestration; do
  echo "=============================================="
  echo "  Trigger-eval: $skill  (model: $MODEL)"
  echo "=============================================="
  ( cd "$SKILL_CREATOR" && python3 -m scripts.run_loop \
      --eval-set   "$REPO_ROOT/$skill/evals/trigger_evals.json" \
      --skill-path "$REPO_ROOT/$skill" \
      --model      "$MODEL" \
      --max-iterations 3 \
      --verbose )
done

echo
echo "Done. Take 'best_description' from each run and paste it into that skill's"
echo "SKILL.md frontmatter, then re-check: <=1024 chars, no angle brackets,"
echo "keeps a 'Do NOT use for...' negative-scope clause."
