#!/usr/bin/env bash
set -euo pipefail

# Installs the Model Routing policy into a CLAUDE.md.
#   ./install.sh                      -> ~/.claude/CLAUDE.md (global, all projects)
#   ./install.sh path/to/CLAUDE.md    -> a single project's CLAUDE.md

TARGET="${1:-$HOME/.claude/CLAUDE.md}"
SNIPPET="$(cd "$(dirname "$0")" && pwd)/rules/model-routing.md"

if [[ ! -f "$SNIPPET" ]]; then
  echo "error: $SNIPPET not found — run from a full clone of the repo" >&2
  exit 1
fi

mkdir -p "$(dirname "$TARGET")"
touch "$TARGET"

if grep -q "^## Model Routing" "$TARGET"; then
  echo "- $TARGET already contains a '## Model Routing' section — nothing to do."
  echo "  (Remove the existing section first to reinstall.)"
  exit 0
fi

{
  echo ""
  cat "$SNIPPET"
} >>"$TARGET"

echo "+ Appended the Model Routing policy to $TARGET"
echo "  It loads into every new Claude Code session."
echo "  Optional: copy agents/*.md into ~/.claude/agents/ for pre-pinned subagents."
