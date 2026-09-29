"""Verify your API key and model output against the real API:  python -m backend.selfcheck"""
import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from . import summarizer  # noqa: E402

SAMPLE = (
    "Cities that added protected bike lanes saw injuries fall by 28 percent over three years. "
    "The study followed 12 mid-sized cities and compared them with 12 similar cities that made no changes. "
    "Researchers found the largest gains near schools and transit stops. Businesses along the new lanes reported "
    "steady or higher sales. The authors caution that results depend on lane design, and painted lines alone "
    "showed little benefit."
)
RESUME = "Ada Lovelace\nSenior Python Engineer\n2016 - Present  Lead Engineer, Analytical Co\n- Cut API latency 40%\n- Led team of 6\nB.Sc Mathematics 2015\nSkills: Python, SQL, AWS, Docker"


async def main() -> int:
    if not os.getenv("ANTHROPIC_API_KEY") or os.getenv("DEMO_MODE") == "1":
        print("Set ANTHROPIC_API_KEY (and unset DEMO_MODE) to run this check.")
        return 1
    c = await summarizer.summarize_content(SAMPLE, "short", "bullets")
    assert c.get("tldr") and c.get("key_points"), "content result missing fields"
    bad = [h for h in c.get("highlights", []) if h.lower() not in SAMPLE.lower()]
    print("content OK:", c["title"], "| highlights not verbatim:", len(bad))
    r = await summarizer.summarize_resume(RESUME, "Python engineer with AWS")
    assert r.get("summary") and r.get("job_match"), "resume result missing fields"
    print("resume OK:", r["name"], "| match", r["job_match"]["score"])
    print("All good with model", summarizer.MODEL)
    return 0


sys.exit(asyncio.run(main()))
