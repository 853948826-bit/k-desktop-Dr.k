# run_full_experiment.py
"""
Full κ-Desktop experiment with Ollama LLM backend.
Runs enough iterations to observe gas→liquid→crystal transitions.
Collects data for paper v3.
"""

import json
import os
import sys
import time
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from black_box import KappaRouter

def run_experiment():
    print("="*70)
    print("κ-Desktop Full Experiment — Ollama LLM Backend")
    print("="*70)
    
    router = KappaRouter(llm_backend="ollama")
    
    # ════════════════════════════════════════
    # Phase 1: Task A — enough reps to reach Crystal
    # ════════════════════════════════════════
    task_a = "Open browser and search for AI"
    task_b = "Open notepad and type hello world"
    task_c = "Create a folder called experiment_output"
    
    all_instructions = []
    
    # Task A: 10 repetitions (need 6+ successes for crystal)
    for _ in range(10):
        all_instructions.append(("A", task_a))
    
    # Task B: 10 repetitions
    for _ in range(10):
        all_instructions.append(("B", task_b))
    
    # Novel task (should trigger gas phase)
    all_instructions.append(("C", task_c))
    all_instructions.append(("C", task_c))
    all_instructions.append(("C", task_c))
    
    # Impossible task (should stay in gas)
    all_instructions.append(("D", "Open quantum computer"))
    all_instructions.append(("D", "Open quantum computer"))
    
    # ════════════════════════════════════════
    # Run all instructions
    # ════════════════════════════════════════
    results = []
    
    print(f"\nRunning {len(all_instructions)} instructions...\n")
    print(f"{'#':>3} {'Task':>4} {'Instruction':<45} {'Path':<22} "
          f"{'κ_before':>8} {'κ_after':>8} {'Phase':<8} {'n':>3} {'PT'}")
    print("-" * 120)
    
    for i, (task_id, instruction) in enumerate(all_instructions, 1):
        result = router.process(instruction)
        
        pt = ""
        if "phase_transition" in result:
            pt = f"⚡ {result['phase_transition']['type']}"
        
        print(f"{i:3d} {task_id:>4} {instruction:<45} {result['path']:<22} "
              f"{result['kappa_before']:8.4f} {result['kappa_after']:8.4f} "
              f"{result['phase']:<8} {result['n']:3d} {pt}")
        
        results.append({
            "iteration": i,
            "task_id": task_id,
            "instruction": instruction,
            "path": result["path"],
            "kappa_before": result["kappa_before"],
            "kappa_after": result["kappa_after"],
            "phase": result["phase"],
            "n": result["n"],
            "success": result["success"],
            "tokens_used": result["tokens_used"],
            "latency_ms": result["latency_ms"],
            "phase_transition": result.get("phase_transition", {}).get("type", None),
        })
    
    # ════════════════════════════════════════
    # Summary
    # ════════════════════════════════════════
    print("\n" + "="*70)
    print("EXPERIMENT SUMMARY")
    print("="*70)
    
    # Per-task summary
    task_summary = {}
    for r in results:
        tid = r["task_id"]
        if tid not in task_summary:
            task_summary[tid] = {
                "instruction": r["instruction"],
                "attempts": 0,
                "successes": 0,
                "final_kappa": 0,
                "final_phase": "",
                "final_n": 0,
                "transitions": [],
                "total_tokens": 0,
                "total_latency": 0,
            }
        ts = task_summary[tid]
        ts["attempts"] += 1
        if r["success"]:
            ts["successes"] += 1
        ts["final_kappa"] = r["kappa_after"]
        ts["final_phase"] = r["phase"]
        ts["final_n"] = r["n"]
        ts["total_tokens"] += r["tokens_used"]
        ts["total_latency"] += r["latency_ms"]
        if r["phase_transition"]:
            ts["transitions"].append(r["phase_transition"])
    
    print(f"\n{'Task':<6} {'Instruction':<40} {'Attempts':>8} {'Success':>8} "
          f"{'κ_final':>8} {'Phase':<8} {'n':>3} {'Transitions'}")
    print("-" * 110)
    
    total_transitions = 0
    for tid, ts in sorted(task_summary.items()):
        trans_str = ", ".join(ts["transitions"]) if ts["transitions"] else "none"
        total_transitions += len(ts["transitions"])
        print(f"{tid:<6} {ts['instruction']:<40} {ts['attempts']:>8} "
              f"{ts['successes']:>8} {ts['final_kappa']:8.4f} "
              f"{ts['final_phase']:<8} {ts['final_n']:3d} {trans_str}")
    
    # Theoretical vs measured κ
    print(f"\n{'='*70}")
    print("κ THEORY vs MEASURED")
    print(f"{'='*70}")
    print(f"{'Task':<6} {'n':>3} {'κ_theory':>10} {'κ_measured':>12} "
          f"{'Error':>8} {'Phase_theory':<14} {'Phase_actual':<14}")
    print("-" * 75)
    
    kappa_max = 0.95
    kappa_min = 0.05
    lam = 0.25
    kc1, kc2 = 0.3, 0.8
    
    theory_data = []
    for tid, ts in sorted(task_summary.items()):
        n = ts["final_n"]
        kappa_theory = kappa_max * (1 - math.exp(-lam * n)) + kappa_min
        kappa_measured = ts["final_kappa"]
        error = abs(kappa_theory - kappa_measured)
        
        def get_phase(k):
            if k >= kc2: return "crystal"
            elif k >= kc1: return "liquid"
            else: return "gas"
        
        phase_theory = get_phase(kappa_theory)
        phase_actual = ts["final_phase"]
        
        print(f"{tid:<6} {n:3d} {kappa_theory:10.4f} {kappa_measured:12.4f} "
              f"{error:8.4f} {phase_theory:<14} {phase_actual:<14}")
        
        theory_data.append({
            "task_id": tid,
            "n": n,
            "kappa_theory": round(kappa_theory, 4),
            "kappa_measured": round(kappa_measured, 4),
            "error": round(error, 4),
        })
    
    # LLM usage stats
    print(f"\n{'='*70}")
    print("LLM USAGE STATISTICS")
    print(f"{'='*70}")
    stats = router.black_box.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")
    
    # Phase transitions
    print(f"\n{'='*70}")
    print(f"PHASE TRANSITIONS: {total_transitions} total")
    print(f"{'='*70}")
    for i, t in enumerate(router.transition_log, 1):
        print(f"  {i}. {t['type']} | κ: {t['kappa_before']:.4f} → "
              f"{t['kappa_after']:.4f} | n={t['n']} | "
              f"{t['instruction'][:40]}")
    
    # ════════════════════════════════════════
    # Save data
    # ════════════════════════════════════════
    os.makedirs("data", exist_ok=True)
    
    export = {
        "experiment": "full_llm_experiment",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "backend": stats,
        "parameters": {
            "kappa_max": kappa_max,
            "kappa_min": kappa_min,
            "lambda": lam,
            "kc1": kc1,
            "kc2": kc2,
        },
        "results": results,
        "task_summary": {k: {**v, "transitions": v["transitions"]} 
                        for k, v in task_summary.items()},
        "theory_vs_measured": theory_data,
        "phase_transitions": [
            {
                "type": t["type"],
                "kappa_before": t["kappa_before"],
                "kappa_after": t["kappa_after"],
                "n": t["n"],
                "instruction": t["instruction"],
            }
            for t in router.transition_log
        ],
    }
    
    filepath = "data/full_experiment_ollama.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(export, f, indent=2, default=str)
    
    print(f"\n✅ Data saved to {filepath}")
    print(f"\n{'='*70}")
    print(f"CONCLUSION")
    print(f"{'='*70}")
    print(f"  Total instructions: {len(results)}")
    print(f"  Total successes:    {sum(1 for r in results if r['success'])}")
    print(f"  Phase transitions:  {total_transitions}")
    print(f"  Unique tasks:       {len(task_summary)}")
    
    # Check if we achieved crystal phase
    crystal_tasks = [tid for tid, ts in task_summary.items() 
                     if ts["final_phase"] == "crystal"]
    if crystal_tasks:
        print(f"  🔵 Crystal phase reached: {crystal_tasks}")
    else:
        max_kappa = max(ts["final_kappa"] for ts in task_summary.values())
        max_n = max(ts["final_n"] for ts in task_summary.values())
        print(f"  ⚠️ Crystal phase not yet reached")
        print(f"     Max κ = {max_kappa:.4f}, Max n = {max_n}")
        needed = math.ceil(-math.log(1 - (0.8 - 0.05) / 0.95) / 0.25)
        print(f"     Need n ≥ {needed} successes for crystal phase")
    
    return router, results


if __name__ == "__main__":
    run_experiment()