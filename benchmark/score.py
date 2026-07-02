#!/usr/bin/env python3
"""Aggregate routed-mix vs all-Fable across N trials.
Per cell: mean cost, pass-rate over trials. Objective (locate/count) scored by ground truth;
interpretive by the hardened 3-sample judge (.judge files)."""
import json, os, re, glob, statistics as st

BENCH = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(BENCH, "results")
QS = json.load(open(os.path.join(BENCH, "questions.json")))
BASELINE = "fable"

def load_result(path):
    data = json.load(open(path))
    if isinstance(data, dict): return data
    for it in reversed(data):
        if isinstance(it, dict) and it.get("type") == "result": return it
    return {}

def answer_and_count(t):
    m = re.findall(r"ANSWER[^:]*:\s*(.+)", t or "")
    return (m[0].strip() if m else ((t or "").strip().splitlines()[-1] if (t or "").strip() else "")), len(m)

def correct_objective(q, ans):
    if q["type"] == "locate":
        gt = q["ground_truth_files"]; a = ans.lower()
        return all(f.lower() in a or os.path.basename(f).lower() in a for f in gt)
    if q["type"] == "count":
        nums = re.findall(r"-?\d+", ans.replace(",", ""))
        return bool(nums) and abs(int(nums[0]) - q["ground_truth_count"]) <= 2
    return False

def cell(q, model):
    """Aggregate all trials for one (question, model). Returns dict or None."""
    files = sorted(glob.glob(os.path.join(RESULTS, f"{q['id']}__{model}__t*.json")))
    if not files: return None
    costs, outs, oks, contaminated = [], [], [], 0
    for f in files:
        r = load_result(f); text = r.get("result", "")
        ans, nans = answer_and_count(text)
        if nans > 1: contaminated += 1; continue
        if isinstance(r.get("total_cost_usd"), (int, float)): costs.append(r["total_cost_usd"])
        u = r.get("usage", {}) or {}
        if isinstance(u.get("output_tokens"), int): outs.append(u["output_tokens"])
        t = re.search(r"__t(\d+)\.json$", f).group(1)
        if q["type"] == "judge":
            jp = os.path.join(RESULTS, f"{q['id']}__{model}__t{t}.judge")
            oks.append(bool(json.load(open(jp)).get("pass")) if os.path.exists(jp) else False)
        else:
            oks.append(correct_objective(q, ans))
    n = len(oks)
    return dict(n=n, cont=contaminated,
                mean_cost=st.mean(costs) if costs else 0.0,
                mean_out=int(st.mean(outs)) if outs else 0,
                passes=sum(oks), passrate=(sum(oks)/n if n else 0.0))

print(f"\n{'question':<22}{'class':<10}{'arm':<9}{'model':<8}{'pass/n':<8}{'mean$':<9}{'out':<7}{'cont':<5}")
print("-"*78)
arms = {"routed": dict(cost=0.0, passes=0, trials=0, out=0),
        "baseline": dict(cost=0.0, passes=0, trials=0, out=0)}
for q in QS:
    for arm, model in [("routed", q["routed_model"]), ("baseline", BASELINE)]:
        c = cell(q, model)
        if not c:
            print(f"{q['id']:<22}{q['class']:<10}{arm:<9}{model:<8}{'MISSING':<8}"); continue
        print(f"{q['id']:<22}{q['class']:<10}{arm:<9}{model:<8}{str(c['passes'])+'/'+str(c['n']):<8}{c['mean_cost']:<9.4f}{c['mean_out']:<7}{c['cont']:<5}")
        a = arms[arm]
        a["cost"] += c["mean_cost"]; a["passes"] += c["passes"]; a["trials"] += c["n"]; a["out"] += c["mean_out"]

print(f"\n=== ARMS across the {len(QS)}-task mix (cost = mean $ for one full pass; quality = pass-rate over all task-trials) ===")
print(f"{'arm':<12}{'quality':<14}{'cost/pass':<12}{'out_tok':<9}")
print("-"*47)
for arm in ("routed", "baseline"):
    a = arms[arm]
    q = f"{a['passes']}/{a['trials']} ({100*a['passes']/a['trials']:.0f}%)" if a['trials'] else "-"
    print(f"{arm:<12}{q:<14}{a['cost']:<12.4f}{a['out']:<9}")

R, B = arms["routed"], arms["baseline"]
if B["cost"] > 0:
    save = 1 - R["cost"]/B["cost"]
    print(f"\nRouted mix vs all-Fable:  {save*100:.0f}% cheaper per full pass  (${R['cost']:.3f} vs ${B['cost']:.3f})")
    print(f"Quality:  routed {100*R['passes']/R['trials']:.0f}%  vs  baseline {100*B['passes']/B['trials']:.0f}%  (over {R['trials']} task-trials/arm)")
