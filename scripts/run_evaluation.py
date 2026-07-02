"""
Evaluation Runner — Phase 5

Runs the full pipeline against evaluation_set.json and produces
a detailed report with relevance scores and latency metrics.
"""

import json
import time
import os
import sys
import logging
from datetime import datetime

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from backend.app.db import pool
from backend.app.orchestrator import run_orchestration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def evaluate_relevance(result_itinerary, expected_categories, expected_keywords):
    """
    Checks:
    1. Category overlap: do any returned places match expected categories?
    2. Keyword overlap: do place names/descriptions contain expected keywords?
    Returns a dict with scores.
    """
    returned_categories = set()
    returned_text = ""
    
    for stop in result_itinerary:
        if stop.category:
            returned_categories.add(stop.category.lower())
        returned_text += f" {stop.name} {stop.description or ''} ".lower()
    
    # Category relevance
    expected_cats = set(c.lower() for c in expected_categories)
    cat_overlap = len(returned_categories & expected_cats)
    cat_score = cat_overlap / len(expected_cats) if expected_cats else 0
    
    # Keyword relevance
    kw_hits = sum(1 for kw in expected_keywords if kw.lower() in returned_text)
    kw_score = kw_hits / len(expected_keywords) if expected_keywords else 0
    
    return {
        "category_score": round(cat_score, 2),
        "keyword_score": round(kw_score, 2),
        "combined_score": round((cat_score + kw_score) / 2, 2),
        "matched_categories": list(returned_categories & expected_cats),
        "matched_keywords": [kw for kw in expected_keywords if kw.lower() in returned_text],
    }


def evaluate_story_quality(itinerary):
    """
    Simple rubric-based check for story quality:
    - Has content (not empty)
    - Reasonable length (50+ chars)
    - Contains the place name
    """
    scores = []
    for stop in itinerary:
        story = stop.story or ""
        score = 0
        if len(story) > 0: score += 1        # Has content
        if len(story) > 50: score += 1        # Meaningful length
        if stop.name.lower().split()[0] in story.lower(): score += 1  # Mentions place
        scores.append(score / 3.0)
    
    return round(sum(scores) / len(scores), 2) if scores else 0


def run_evaluation():
    eval_path = os.path.join(os.path.dirname(__file__), "evaluation_set.json")
    with open(eval_path, "r", encoding="utf-8") as f:
        eval_set = json.load(f)
    
    pool.open()
    
    results = []
    all_latencies = []
    successes = 0
    failures = 0
    
    print(f"\n{'='*70}")
    print(f"  CULTURAL RECOMMENDER — EVALUATION RUN")
    print(f"  {datetime.now().isoformat()}")
    print(f"  {len(eval_set)} test queries")
    print(f"{'='*70}\n")
    
    for i, test_case in enumerate(eval_set):
        query_id = test_case["id"]
        query = test_case["query"]
        expected_cats = test_case["expected_categories"]
        expected_kws = test_case["expected_keywords"]
        lang = test_case["language"]
        
        print(f"[{i+1}/{len(eval_set)}] Testing: \"{query[:60]}...\" ({lang})")
        
        try:
            response = run_orchestration(query)
            latency = getattr(run_orchestration, '_last_latency', {})
            
            relevance = evaluate_relevance(response.itinerary, expected_cats, expected_kws)
            story_quality = evaluate_story_quality(response.itinerary)
            
            result = {
                "id": query_id,
                "query": query,
                "language": lang,
                "status": "success",
                "num_stops": len(response.itinerary),
                "places_returned": [s.name for s in response.itinerary],
                "relevance": relevance,
                "story_quality_score": story_quality,
                "latency": latency,
            }
            results.append(result)
            all_latencies.append(latency)
            successes += 1
            
            print(f"   [SUCCESS] Relevance: {relevance['combined_score']:.0%} | "
                  f"Story: {story_quality:.0%} | "
                  f"E2E: {latency.get('total_e2e_ms', '?')}ms")
            
        except Exception as e:
            failures += 1
            results.append({
                "id": query_id,
                "query": query,
                "language": lang,
                "status": "failed",
                "error": str(e),
            })
            print(f"   [FAILED] {e}")
    
    pool.close()
    
    # ---- Aggregate Metrics ----
    successful_results = [r for r in results if r["status"] == "success"]
    
    avg_relevance = sum(r["relevance"]["combined_score"] for r in successful_results) / len(successful_results) if successful_results else 0
    avg_story = sum(r["story_quality_score"] for r in successful_results) / len(successful_results) if successful_results else 0
    
    # Latency stats
    if all_latencies:
        e2e_times = sorted([l.get("total_e2e_ms", 0) for l in all_latencies])
        p50_idx = len(e2e_times) // 2
        p95_idx = int(len(e2e_times) * 0.95)
        
        latency_summary = {
            "avg_e2e_ms": round(sum(e2e_times) / len(e2e_times)),
            "p50_e2e_ms": e2e_times[p50_idx],
            "p95_e2e_ms": e2e_times[min(p95_idx, len(e2e_times)-1)],
            "avg_preference_agent_ms": round(sum(l.get("preference_agent_ms", 0) for l in all_latencies) / len(all_latencies)),
            "avg_retrieval_ms": round(sum(l.get("retrieval_ms", 0) for l in all_latencies) / len(all_latencies)),
            "avg_crowd_estimator_ms": round(sum(l.get("crowd_estimator_ms", 0) for l in all_latencies) / len(all_latencies)),
            "avg_recommender_agent_ms": round(sum(l.get("recommender_agent_ms", 0) for l in all_latencies) / len(all_latencies)),
            "avg_story_generator_ms": round(sum(l.get("story_generator_ms", 0) for l in all_latencies) / len(all_latencies)),
        }
    else:
        latency_summary = {}
    
    report = {
        "run_date": datetime.now().isoformat(),
        "total_queries": len(eval_set),
        "successes": successes,
        "failures": failures,
        "success_rate": round(successes / len(eval_set), 2),
        "avg_relevance_score": round(avg_relevance, 2),
        "avg_story_quality_score": round(avg_story, 2),
        "latency_summary": latency_summary,
        "detailed_results": results,
    }
    
    # Save report
    report_path = os.path.join("reports", f"evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    os.makedirs("reports", exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"  EVALUATION SUMMARY")
    print(f"{'='*70}")
    print(f"  Success Rate:        {successes}/{len(eval_set)} ({report['success_rate']:.0%})")
    print(f"  Avg Relevance Score: {avg_relevance:.0%}")
    print(f"  Avg Story Quality:   {avg_story:.0%}")
    if latency_summary:
        print(f"\n  --- Latency (ms) ---")
        print(f"  Avg E2E:             {latency_summary['avg_e2e_ms']}ms")
        print(f"  P50 E2E:             {latency_summary['p50_e2e_ms']}ms")
        print(f"  P95 E2E:             {latency_summary['p95_e2e_ms']}ms")
        print(f"  Avg Preference Agent:{latency_summary['avg_preference_agent_ms']}ms")
        print(f"  Avg Retrieval:       {latency_summary['avg_retrieval_ms']}ms")
        print(f"  Avg Crowd (XGBoost): {latency_summary['avg_crowd_estimator_ms']}ms")
        print(f"  Avg Recommender:     {latency_summary['avg_recommender_agent_ms']}ms")
        print(f"  Avg Story Generator: {latency_summary['avg_story_generator_ms']}ms")
    print(f"\n  Report saved to: {report_path}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    run_evaluation()
