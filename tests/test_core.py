import pytest

from backend.extract import _is_public_host, clean_text, extract_text
from backend.summarizer import parse_json


def test_parse_json_plain():
    assert parse_json('{"a": 1}') == {"a": 1}


def test_parse_json_fenced_with_preamble():
    assert parse_json('Here you go:\n```json\n{"a": [1, 2]}\n```') == {"a": [1, 2]}


def test_parse_json_rejects_prose():
    with pytest.raises(ValueError):
        parse_json("Sorry, I can't do that.")


def test_extract_txt():
    text = extract_text("notes.txt", b"Hello world. " * 10)
    assert text.startswith("Hello world.")


def test_extract_rejects_unknown_type():
    with pytest.raises(ValueError):
        extract_text("malware.exe", b"x" * 100)


def test_clean_text_collapses_blank_lines():
    assert clean_text("a\n\n\n\nb") == "a\n\nb"


def test_ssrf_blocks_loopback():
    assert _is_public_host("127.0.0.1") is False


def test_unwrap_rejoins_wrapped_pdf_lines_but_keeps_bullets():
    from backend.extract import unwrap_lines

    raw = "Cities that added lanes saw injuries\nfall by 28 percent.\n- Cut cost 35%\n- Led a team"
    assert unwrap_lines(raw) == "Cities that added lanes saw injuries fall by 28 percent.\n- Cut cost 35%\n- Led a team"
