#!/usr/bin/env python3
"""Hardened LLM judge for interpretive answers.
- Mechanism-credit rubric: checks the grounded key_points (yes/no each), NOT exact symbol names.
- 3 judge samples per answer; an answer 'passes' if it covers >= PASS_POINTS key points,
  and the final verdict is the MAJORITY over the 3 samples.
Writes results/<qid>__<model>__t<T>.judge as JSON {covered:[...], pass:bool}. Idempotent."""
import json, os, re, subprocess

BENCH = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(BENCH, "results")
QS = {q["id"]: q for q in json.load(open(os.path.join(BENCH, "questions.json")))}
JUDGE_MODEL = "opus"
SAMPLES = 3
PASS_FRACTION = 2/3   # cover >= 2 of 3 key points to pass

def load_answer(path):
    data = json.load(open(path))
    r = [x for x in data if isinstance(x, dict) and x.get("type") == "result"][-1] if isinstance(data, list) else data
    t = r.get("result", "") or ""
    m = re.findall(r"ANSWER[^:]*:\s*(.+)", t)
    return (m[0].strip() if m else t.strip())

def build_prompt(q, cand):
    pts = "\n".join(f"  {i+1}. {p}" for i, p in enumerate(q["key_points"]))
    return f"""You grade whether a candidate answer about a codebase captures the KEY MECHANISM.
Credit the CONCEPT even if the candidate uses different wording or does not cite exact function/file names.
Do NOT require exact symbol names. Judge only whether each key point's IDEA is present and correct.

QUESTION:
{q['prompt'].split('End your reply')[0].strip()}

KEY POINTS (the correct mechanism):
{pts}

CANDIDATE ANSWER:
{cand}

For each numbered key point, decide if the candidate's answer conveys that idea (correctly).
Output ONLY one line, comma-separated yes/no for each point in order, e.g. for 3 points: VERDICT: yes,no,yes"""

def one_sample(prompt):
    proc = subprocess.run(
        ["claude", "-p", prompt, "--model", JUDGE_MODEL, "--output-format", "json",
         "--strict-mcp-config", "--mcp-config", os.path.join(BENCH, "empty-mcp.json"),
         "--allowedTools", "--dangerously-skip-permissions"],
        cwd="/tmp", capture_output=True, text=True, stdin=subprocess.DEVNULL)
    try:
        data = json.loads(proc.stdout)
        r = [x for x in data if isinstance(x, dict) and x.get("type") == "result"][-1] if isinstance(data, list) else data
        txt = r.get("result", "")
    except Exception:
        txt = proc.stdout
    m = re.findall(r"VERDICT:\s*([yesno, ]+)", txt, re.I)
    if not m: return None
    toks = [t.strip().lower() for t in m[-1].split(",")]
    return [t.startswith("y") for t in toks]

def judge_answer(q, model, trial):
    outp = os.path.join(RESULTS, f"{q['id']}__{model}__t{trial}.judge")
    if os.path.exists(outp):
        return json.load(open(outp))
    resp = os.path.join(RESULTS, f"{q['id']}__{model}__t{trial}.json")
    if not os.path.exists(resp): return None
    cand = load_answer(resp)
    prompt = build_prompt(q, cand)
    n_pts = len(q["key_points"]); need = int(round(n_pts * PASS_FRACTION))
    sample_pass = []; covered_counts = []
    for _ in range(SAMPLES):
        v = one_sample(prompt)
        if v is None: continue
        c = sum(v[:n_pts])
        covered_counts.append(c)
        sample_pass.append(c >= need)
    passed = sample_pass.count(True) > len(sample_pass)/2 if sample_pass else False
    out = {"covered_counts": covered_counts, "need": need, "n_pts": n_pts,
           "samples_pass": sample_pass, "pass": passed}
    json.dump(out, open(outp, "w"))
    print(f"  judged {q['id']}/{model}/t{trial}: covered {covered_counts} need>={need} -> {'PASS' if passed else 'FAIL'}")
    return out

if __name__ == "__main__":
    trials = int(os.environ.get("TRIALS", "3"))
    for qid, q in QS.items():
        if q.get("type") != "judge": continue
        for model in [q["routed_model"], "fable"]:
            for t in range(1, trials+1):
                judge_answer(q, model, t)
    print("judging done")
