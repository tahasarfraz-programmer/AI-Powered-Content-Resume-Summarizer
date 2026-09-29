from backend.demo import demo_content, demo_resume

ARTICLE = (
    "Protected bike lanes cut injuries\n\n"
    "Cities that added protected bike lanes saw injuries fall by 28 percent over three years. "
    "The study followed twelve mid-sized cities and compared them with similar cities that made no changes. "
    "Researchers found the largest gains near schools and transit stops in every city studied. "
    "Businesses along the new lanes reported steady or higher sales after installation. "
    "The authors caution that results depend on lane design and painted lines alone showed little benefit."
)


def test_demo_content_shape_and_verbatim_highlights():
    r = demo_content(ARTICLE, "medium")
    assert r["title"] == "Protected bike lanes cut injuries"
    assert r["tldr"] and r["key_points"] and r["demo"]
    assert all(h in ARTICLE for h in r["highlights"])


def test_demo_resume_with_job():
    cv = "Ada Lovelace\n2016 - Present Lead Engineer\n- Cut latency 40%\nB.Sc Mathematics 2015\nPython, SQL, AWS, leadership"
    r = demo_resume(cv, "Need Python and AWS and Kubernetes")
    assert r["name"] == "Ada Lovelace"
    assert "Python" in r["skills"]["technical"]
    assert r["job_match"]["matched"] == ["AWS", "Python"] and r["job_match"]["missing"] == ["Kubernetes"]
    assert r["experience"][0]["highlights"] == ["Cut latency 40%"]
