from __future__ import annotations
from graph import app


def run_task(task: str):
    result = app.invoke(
        {
            "messages": [],
            "task": task,
            "research_findings": None,
            "analysis": None,
            "draft": None,
            "final_answer": None,
            "next_agent": None,
            "error": None,
        },
        {"recursion_limit": 15},
    )

    print("\n" + "=" * 60)
    print("RESEARCH FINDINGS:")
    print("=" * 60)
    print(result.get("research_findings", "N/A"))

    print("\n" + "=" * 60)
    print("ANALYSIS:")
    print("=" * 60)
    print(result.get("analysis", "N/A"))

    print("\n" + "=" * 60)
    print("FINAL ANSWER:")
    print("=" * 60)
    print(result.get("final_answer", "No output"))

    if result.get("error"):
        print(f"\n⚠️  {result['error']}")

    return result


if __name__ == "__main__":
    run_task(
        "Should we build a custom AI chatbot or buy SaaS? "
        "Budget $50k/year, 2 ML engineers."
    )