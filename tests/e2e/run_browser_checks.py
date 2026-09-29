import re, sys
from playwright.sync_api import sync_playwright

URL = "http://localhost:8765/"
results, errors = [], []
def check(name, cond, extra=""):
    results.append((name, bool(cond))); print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1360, "height": 900}, accept_downloads=True)
    ctx.grant_permissions(["clipboard-read", "clipboard-write"])
    pg = ctx.new_page()
    pg.on("response", lambda r: errors.append(f"{r.status} {r.url}") if r.status >= 400 and "fonts.g" not in r.url and "/api/summarize/" not in r.url else None)
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(URL); pg.wait_for_timeout(2600)
    check("example loads with highlights", pg.locator("#source mark").count() == 4)
    check("demo badge shown", "Demo mode" in pg.inner_text("#mode-badge"))
    pg.screenshot(path="/tmp/shots/01_home.png", full_page=True)

    # empty validation
    pg.click("#go"); check("empty submit shows error", "Add at least" in pg.inner_text("#error"))

    # pasted text flow
    pg.click("#use-example"); check("word counter updates", "words" in pg.inner_text("#wc") and pg.inner_text("#wc")[0] != "0")
    held = []
    pg.route("**/api/summarize/content", lambda r: held.append(r))
    pg.click("#go"); pg.wait_for_timeout(600)
    check("loading skeleton shown", pg.locator("#summary .sk").count() > 0 and pg.is_disabled("#go") and pg.locator("#source .scan").count() == 1)
    pg.screenshot(path="/tmp/shots/02_loading.png")
    held[0].continue_(); pg.unroute("**/api/summarize/content")
    pg.wait_for_selector("#summary .tldr", timeout=10000); pg.wait_for_timeout(2500)
    check("text result rendered", pg.locator("#summary .pts li").count() >= 3)
    check("basic-summary tag shown", "Basic summary" in pg.inner_text("#summary"))
    check("highlights present in original", pg.locator("#source mark").count() >= 2)
    pg.click("#next"); check("highlight nav works", pg.locator("#source mark.on").count() == 1)
    pg.screenshot(path="/tmp/shots/03_content_result.png", full_page=True)
    pg.click("#copy"); check("copy summary", len(pg.evaluate("navigator.clipboard.readText()")) > 40)
    with pg.expect_download() as d: pg.click("#dl")
    check("download .md", d.value.suggested_filename == "summary.md")

    # PDF upload
    pg.set_input_files("#file", "/tmp/fx/article.pdf"); check("file chip shows name", "article.pdf" in pg.inner_text("#drop"))
    pg.fill("#text", ""); pg.select_option("#length", "short"); pg.click("#go")
    pg.wait_for_function("document.querySelector('#summary .title') && !document.querySelector('#summary .sk')", timeout=10000)
    check("PDF summarized", "bike lanes" in pg.inner_text("#source").lower(), pg.inner_text("#source")[:80])
    check("PDF lines un-wrapped (sentence intact)", "cyclist injuries fall by 28 percent over three years" in pg.inner_text("#source"))
    check("highlight tolerates newline vs space", pg.evaluate('highlightHtml("alpha beta\\ngamma delta", ["beta gamma"])').count("<mark") == 1)
    pg.click("#rm"); check("file removable", pg.locator("#drop .filechip").count() == 0)

    # bad file type surfaces a friendly error
    pg.set_input_files("#file", "/tmp/fx/bad.exe"); pg.click("#go"); pg.wait_for_timeout(1200)
    check("bad file type error", "Unsupported file type" in pg.inner_text("#error"), pg.inner_text("#error"))
    pg.click("#rm")

    # SSRF blocked
    pg.fill("#url", "http://127.0.0.1:8765/"); pg.click("#go"); pg.wait_for_timeout(1200)
    check("private URL blocked", "can't be fetched" in pg.inner_text("#error"), pg.inner_text("#error"))
    pg.fill("#url", "")

    # resume tab with docx + JD
    pg.click("#tab-resume"); pg.wait_for_timeout(2400)
    check("resume example ring shows 84", pg.inner_text("#num") == "84", pg.inner_text("#num"))
    pg.screenshot(path="/tmp/shots/04_resume_example.png", full_page=True)
    pg.set_input_files("#file", "/tmp/fx/cv.docx"); pg.fill("#text", "")
    pg.fill("#jd", "Looking for a data engineer with Python, SQL, AWS and Kubernetes. Leadership a plus.")
    pg.click("#go"); pg.wait_for_function("document.querySelector('#summary .who') && !document.querySelector('#summary .sk')", timeout=10000)
    pg.wait_for_timeout(2200)
    check("acronym casing (AWS)", "AWS" in pg.inner_text("#summary"), pg.inner_text("#summary")[:200])
    check("DOCX parsed name", "Ngozi Adeyemi" in pg.inner_text("#summary .who"), pg.inner_text("#summary .who"))
    check("DOCX experience parsed", pg.locator("#summary .role").count() >= 2)
    check("job match score animated", pg.inner_text("#num").isdigit() and int(pg.inner_text("#num")) > 0, pg.inner_text("#num"))
    check("missing skill flagged", "kubernetes" in pg.inner_text("#summary").lower())
    pg.screenshot(path="/tmp/shots/05_resume_result.png", full_page=True)

    # tab switch keeps results
    pg.click("#tab-content"); pg.wait_for_timeout(600)
    check("content tab restores result", pg.locator("#summary .pts li").count() >= 3)
    pg.wait_for_timeout(2500)

    # dark mode + mobile
    pg.click("#theme"); pg.wait_for_timeout(500)
    check("dark theme applied", pg.evaluate("document.documentElement.dataset.theme") == "dark")
    pg.screenshot(path="/tmp/shots/06_dark.png", full_page=True)
    m = ctx.new_page(); m.set_viewport_size({"width": 390, "height": 844}); m.goto(URL); m.wait_for_timeout(2400)
    check("mobile: no horizontal scroll", m.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), str(m.evaluate("document.documentElement.scrollWidth")))
    m.screenshot(path="/tmp/shots/07_mobile.png", full_page=True)
    b.close()

check("no console/page errors", not errors, "; ".join(errors))
print(f"\n{sum(ok for _, ok in results)}/{len(results)} checks passed")
sys.exit(0 if all(ok for _, ok in results) else 1)
