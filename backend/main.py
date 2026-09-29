"""AI-Powered Content & Resume Summarizer (FastAPI)."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import anthropic  # noqa: E402
import httpx  # noqa: E402
from fastapi import FastAPI, File, Form, HTTPException, UploadFile  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from . import summarizer  # noqa: E402
from .extract import extract_text, fetch_url  # noqa: E402

MAX_UPLOAD = int(os.getenv("MAX_UPLOAD_MB", "8")) * 1024 * 1024
FRONTEND = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(title="AI-Powered Content & Resume Summarizer", version="1.0.0")


async def resolve_input(text: str | None, url: str | None, file: UploadFile | None) -> str:
    """Pick the input source: file, then URL, then pasted text."""
    try:
        if file is not None and file.filename:
            data = await file.read()
            if len(data) > MAX_UPLOAD:
                raise HTTPException(413, f"File is larger than {MAX_UPLOAD // 1024 // 1024} MB.")
            return extract_text(file.filename, data)
        if url and url.strip():
            return await fetch_url(url)
    except httpx.HTTPError:
        raise HTTPException(400, "Couldn't load that link. Check the address and try again.")
    except ValueError as e:
        raise HTTPException(400, str(e))
    if text and len(text.strip()) >= 30:
        return text.strip()
    raise HTTPException(400, "Add some text, a link, or a file to summarize.")


async def call_llm(fn, *args):
    try:
        return await fn(*args)
    except anthropic.AuthenticationError:
        raise HTTPException(500, "The server's API key is missing or invalid.")
    except anthropic.RateLimitError:
        raise HTTPException(429, "Too many requests. Try again in a minute.")
    except (anthropic.APIError, ValueError):
        raise HTTPException(502, "The summarizer returned an unusable answer. Try again.")


@app.post("/api/summarize/content")
async def summarize_content(
    text: str | None = Form(None),
    url: str | None = Form(None),
    length: str = Form("medium"),
    style: str = Form("bullets"),
    file: UploadFile | None = File(None),
):
    source = await resolve_input(text, url, file)
    result = await call_llm(summarizer.summarize_content, source, length, style)
    result["source_text"] = source
    return result


@app.post("/api/summarize/resume")
async def summarize_resume(
    text: str | None = Form(None),
    job_description: str | None = Form(None),
    file: UploadFile | None = File(None),
):
    source = await resolve_input(text, None, file)
    result = await call_llm(summarizer.summarize_resume, source, job_description)
    result["source_text"] = source
    return result


@app.get("/api/health")
async def health():
    return {"ok": True, "model": summarizer.MODEL, "demo": summarizer.is_demo()}


@app.get("/")
async def index():
    return FileResponse(FRONTEND / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND), name="static")
