"""Thin wrapper around the Anthropic API that returns parsed JSON."""
import json
import os
import re

from anthropic import AsyncAnthropic

from .prompts import CONTENT_SYSTEM, RESUME_SYSTEM, content_user, resume_user

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
MAX_INPUT_CHARS = int(os.getenv("MAX_INPUT_CHARS", "60000"))

_client: AsyncAnthropic | None = None


def get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic()  # reads ANTHROPIC_API_KEY
    return _client


def parse_json(text: str) -> dict:
    """Parse model output, tolerating stray markdown fences or preamble."""
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Model did not return JSON.")
    return json.loads(text[start : end + 1])


async def _run(system: str, user: str, max_tokens: int) -> dict:
    resp = await get_client().messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text")
    return parse_json(text)


def _trim(text: str) -> tuple[str, bool]:
    if len(text) <= MAX_INPUT_CHARS:
        return text, False
    return text[:MAX_INPUT_CHARS], True


def is_demo() -> bool:
    return os.getenv("DEMO_MODE") == "1" or not os.getenv("ANTHROPIC_API_KEY")


async def summarize_content(text: str, length: str, style: str) -> dict:
    trimmed, truncated = _trim(text)
    if is_demo():
        from .demo import demo_content

        return {**demo_content(trimmed, length), "truncated": truncated}
    result = await _run(CONTENT_SYSTEM, content_user(trimmed, length, style), 1800)
    result["truncated"] = truncated
    return result


async def summarize_resume(text: str, job_description: str | None) -> dict:
    trimmed, truncated = _trim(text)
    if is_demo():
        from .demo import demo_resume

        return {**demo_resume(trimmed, job_description), "truncated": truncated}
    jd = job_description[:12000] if job_description else None
    result = await _run(RESUME_SYSTEM, resume_user(trimmed, jd), 2500)
    result["truncated"] = truncated
    return result
