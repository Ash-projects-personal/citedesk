"""Run CiteDesk against the authored eval set and record measured results.

Usage: python3 eval/run_eval.py
Writes eval/results.json and prints a summary. Numbers are measured, never
rounded up or adjusted.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bot import Bot

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    bot = Bot()
    with open(os.path.join(HERE, "questions.json")) as f:
        spec = json.load(f)
    rows = []
    stats = {"answer_ok": 0, "answer_wrong": 0, "escalate_ok": 0, "escalate_missed": 0}
    for item in spec["questions"]:
        res = bot.ask(item["q"])
        if item["expect"] == "answer":
            ok = res["type"] == "answer" and item["article"] in res["citations"]
            key = "answer_ok" if ok else "answer_wrong"
            got_article = res["citations"][0] if res["type"] == "answer" else None
        else:
            ok = res["type"] == "escalation"
            key = "escalate_ok" if ok else "escalate_missed"
            got_article = res["citations"][0] if res["type"] == "answer" else None
        stats[key] += 1
        rows.append(
            {
                "q": item["q"],
                "expect": item["expect"],
                "expected_article": item.get("article"),
                "got": res["type"],
                "top_citation": got_article,
                "groundedness": res.get("groundedness"),
                "evidence_score": res.get("evidence_score"),
                "correct": ok,
            }
        )
    stats["total"] = len(rows)
    stats["correct"] = stats["answer_ok"] + stats["escalate_ok"]
    with open(os.path.join(HERE, "results.json"), "w") as f:
        json.dump({"stats": stats, "rows": rows}, f, indent=2)
    print(json.dumps(stats, indent=2))
    for r in rows:
        if not r["correct"]:
            print("MISS:", r)


if __name__ == "__main__":
    main()
