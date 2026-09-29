"""Offline fallback used when no ANTHROPIC_API_KEY is set (or DEMO_MODE=1).

This is a plain extractive heuristic, not AI. It exists so the app runs and can be
tested without a key. The UI labels the result clearly as a basic summary.
"""
import re
from collections import Counter
from datetime import datetime

STOP = set(
    "a an the and or but if then of to in on for with as at by from is are was were be been being it its this "
    "that these those i you he she we they them his her our your their not no do does did have has had will would "
    "can could should may might also than so such more most other into about over after before between while "
    "which who whom what when where how there here just very".split()
)

SOFT = {"communication", "leadership", "teamwork", "problem solving", "project management", "agile", "scrum"}
SKILLS = sorted(
    SOFT
    | {
        "python", "java", "javascript", "typescript", "react", "node.js", "sql", "postgresql", "mysql",
        "mongodb", "aws", "azure", "gcp", "docker", "kubernetes", "git", "linux", "django", "flask",
        "fastapi", "machine learning", "deep learning", "nlp", "pytorch", "tensorflow", "pandas",
        "tableau", "power bi", "figma", "c++", "c#", "html", "css", "ci/cd", "graphql", "rust",
        "data analysis", "testing", "devops", "ux design", "seo", "marketing", "sales",
    }
)
DEGREE = re.compile(r"\b(b\.?sc|m\.?sc|b\.?tech|m\.?tech|bachelor|master|ph\.?d|mba|diploma|degree)\b", re.I)
RANGE = re.compile(r"((?:19|20)\d{2})\s*(?:-|–|—|to)\s*((?:19|20)\d{2}|present|current|now)", re.I)


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n{2,}", text)
    sents = [p.strip() for p in parts if 40 <= len(p.strip()) <= 400]
    if len(sents) < 3:
        sents = [ln.strip() for ln in text.split("\n") if len(ln.strip()) >= 25]
    return sents


def _tokens(s: str) -> list[str]:
    return [t for t in re.findall(r"[a-zA-Z']{3,}", s.lower()) if t not in STOP]


def _clip(s: str, max_words: int = 22) -> str:
    words = list(re.finditer(r"\S+", s))
    return s if len(words) <= max_words else s[: words[max_words - 1].end()]


ACRONYMS = {"aws", "sql", "css", "html", "nlp", "gcp", "seo", "ci/cd", "ux design", "c++", "c#", "gpt", "api"}


def _disp(skill: str) -> str:
    if skill in ACRONYMS:
        return skill.upper() if skill != "ux design" else "UX design"
    return skill.title() if " " not in skill else skill.capitalize()


def demo_content(text: str, length: str) -> dict:
    first_line = next((ln.strip() for ln in text.split("\n") if ln.strip()), "")
    has_title = 5 <= len(first_line) <= 80 and not first_line.endswith((".", "!", "?"))
    body = text.split("\n", 1)[1] if has_title and "\n" in text else text
    sents = _sentences(body) or [body[:300]]
    freq = Counter(t for s in sents for t in _tokens(s))
    scores = []
    for i, s in enumerate(sents):
        toks = _tokens(s)
        score = sum(freq[t] for t in toks) / (max(len(toks), 1) ** 0.6)
        scores.append(score * (1.2 if i == 0 else 1.0))
    ranked = sorted(range(len(sents)), key=lambda i: scores[i], reverse=True)

    n_tldr = {"short": 1, "medium": 2, "long": 3}.get(length, 2)
    n_key = {"short": 3, "medium": 5, "long": 8}.get(length, 5)
    tldr_idx = sorted(ranked[:n_tldr])
    key_idx = sorted([i for i in ranked if i not in tldr_idx][:n_key])

    title = first_line if has_title else " ".join(text.split()[:8]) + "…"

    common = [w for w, _ in Counter(t for t in _tokens(text) if len(t) >= 5).most_common(4)]
    return {
        "title": title,
        "tldr": " ".join(sents[i] for i in tldr_idx),
        "key_points": [sents[i] for i in key_idx],
        "topics": [w.title() for w in common],
        "highlights": [_clip(sents[i]) for i in ranked[:5]],
        "demo": True,
    }


def demo_resume(text: str, jd: str | None) -> dict:
    lower = text.lower()
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    first = lines[0] if lines else ""
    name = first if len(first) <= 40 and "@" not in first and not re.search(r"\d", first) else None

    found = [k for k in SKILLS if re.search(r"(?<![a-z])" + re.escape(k) + r"(?![a-z])", lower)]
    soft = [k for k in found if k in SOFT]
    tech = [k for k in found if k not in SOFT]

    year_now = datetime.now().year
    explicit = [int(m) for m in re.findall(r"(\d{1,2})\+?\s*(?:years|yrs)", lower)]
    ranges = [(int(a), year_now if b.lower() in ("present", "current", "now") else int(b)) for a, b in RANGE.findall(text)]
    years = max(explicit) if explicit else (max(b for _, b in ranges) - min(a for a, _ in ranges) if ranges else None)
    seniority = "unknown" if years is None else "junior" if years < 2 else "mid" if years < 5 else "senior" if years < 9 else "lead"

    experience = []
    for i, ln in enumerate(lines):
        m = RANGE.search(ln)
        if not m:
            continue
        bullets = []
        for nxt in lines[i + 1 : i + 6]:
            if RANGE.search(nxt):
                break
            if nxt[:1] in "-•*–·":
                bullets.append(nxt.lstrip("-•*–· ").strip())
        role = RANGE.sub("", ln).strip(" ,|-–—()")
        experience.append({"role": role or "Role", "company": "", "dates": m.group(0), "highlights": bullets[:3]})

    education = []
    for ln in lines:
        if DEGREE.search(ln):
            yr = re.search(r"(?:19|20)\d{2}", ln)
            education.append({"degree": ln[:90], "school": "", "year": yr.group(0) if yr else ""})

    measurable = bool(re.search(r"\d+\s*%|\$\s*\d|\b\d{2,}\b\s*(users|customers|clients|people|projects)", lower))
    strengths = []
    if tech:
        strengths.append("Skills listed: " + ", ".join(_disp(k) for k in tech[:5]))
    if years is not None:
        strengths.append(f"Roughly {years} years of experience")
    if measurable:
        strengths.append("Includes measurable results")
    concerns = []
    if not education:
        concerns.append("No education section detected")
    if not measurable:
        concerns.append("Few measurable results such as percentages or amounts")
    if not experience:
        concerns.append("No dated roles detected")

    job_match = None
    if jd and jd.strip():
        jl = jd.lower()
        req = [k for k in SKILLS if re.search(r"(?<![a-z])" + re.escape(k) + r"(?![a-z])", jl)]
        if not req:
            req = [w for w, _ in Counter(_tokens(jd)).most_common(10)]
        matched = [k for k in req if re.search(r"(?<![a-z])" + re.escape(k) + r"(?![a-z])", lower)]
        missing = [k for k in req if k not in matched]
        score = round(100 * len(matched) / len(req)) if req else 0
        job_match = {
            "score": score,
            "verdict": "strong" if score >= 70 else "possible" if score >= 40 else "weak",
            "matched": [_disp(k) for k in matched],
            "missing": [_disp(k) for k in missing],
            "reasoning": f"{len(matched)} of {len(req)} keywords from the job description appear in the resume.",
        }

    return {
        "name": name,
        "headline": ", ".join(_disp(k) for k in tech[:3]) if tech else "Headline not detected",
        "location": None,
        "summary": f"{name or 'This candidate'} lists {len(found)} recognized skills"
        + (f", including {', '.join(_disp(k) for k in found[:3])}" if found else "")
        + (f", with about {years} years of experience." if years is not None else "."),
        "years_experience": years,
        "seniority": seniority,
        "skills": {"technical": [_disp(k) for k in tech], "soft": [_disp(k) for k in soft], "tools": []},
        "experience": experience[:6],
        "education": education[:3],
        "strengths": strengths,
        "concerns": concerns,
        "improvements": [
            "Add measurable results to each role (percentages, amounts, team sizes)",
            "Open with a two-line professional summary",
            "Group skills by category so they scan quickly",
        ],
        "job_match": job_match,
        "demo": True,
    }
