#!/usr/bin/env bash
# Benchmark runner for agent-model-routing.
# For each task, runs BOTH its policy-routed tier AND the Fable baseline (top tier),
# headless inside the fixture repo. Captures real billed cost + token usage per run.
set -u

BENCH="$(cd "$(dirname "$0")" && pwd)"
FIXTURE="${FIXTURE:-$HOME/antigravity/supabrain-desktop}"
BASELINE="${BASELINE:-fable}"     # the "just use the big model" arm
TRIALS="${TRIALS:-3}"             # repeat each cell N times to average nondeterminism
RESULTS="$BENCH/results"
mkdir -p "$RESULTS"

echo "Fixture:  $FIXTURE"
echo "Baseline: $BASELINE"
echo

# Emit id<TAB>routed_model<TAB>prompt
python3 - "$BENCH/questions.json" <<'PY' > "$BENCH/.qlist"
import json,sys
for q in json.load(open(sys.argv[1])):
    print("\t".join([q["id"], q["routed_model"], q["prompt"]]))
PY

run_one() {  # qid model trial prompt
  local QID="$1" M="$2" T="$3" PROMPT="$4"
  local OUT="$RESULTS/${QID}__${M}__t${T}.json"
  if [ -s "$OUT" ]; then echo "skip (exists): $QID / $M / t$T"; return; fi
  echo ">>> $QID / $M / t$T ..."
  ( cd "$FIXTURE" && claude -p "$PROMPT" \
      --model "$M" \
      --output-format json \
      --strict-mcp-config --mcp-config "$BENCH/empty-mcp.json" \
      --allowedTools "Bash" "Grep" "Glob" "Read" \
      --dangerously-skip-permissions </dev/null ) > "$OUT" 2> "$RESULTS/${QID}__${M}__t${T}.err"
  echo "    exit=$? bytes=$(wc -c < "$OUT" | tr -d ' ')"
}

while IFS=$'\t' read -r QID ROUTED PROMPT <&3; do
  for T in $(seq 1 "$TRIALS"); do
    run_one "$QID" "$ROUTED" "$T" "$PROMPT"                                   # routed arm
    [ "$ROUTED" != "$BASELINE" ] && run_one "$QID" "$BASELINE" "$T" "$PROMPT" # baseline arm
  done
done 3< "$BENCH/.qlist"

echo "Done. Raw results in $RESULTS"
