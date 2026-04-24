"""
E2E tests using Playwright against a live running app.
Requires: BASE_URL env var (default http://localhost:8000) and a real OPENAI_API_KEY.

Run locally:
    uv run pytest tests/e2e/ -v
"""
import os
import pytest
from playwright.sync_api import Page, expect

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

SAMPLE_RESUME = """Jane Smith
jane@email.com | linkedin.com/in/janesmith | San Francisco, CA

SUMMARY
Software engineer with 5 years of experience building scalable backend systems in Python and Go.

EXPERIENCE
Senior Software Engineer — Acme Corp (2021–Present)
• Redesigned data pipeline, reducing processing time by 60%
• Led migration from monolith to microservices (Go, Kubernetes)

Software Engineer — Startup XYZ (2019–2021)
• Built REST APIs serving 500K daily requests (Python, FastAPI)

EDUCATION
B.S. Computer Science — UC Berkeley, 2019

SKILLS
Python, Go, TypeScript, Kubernetes, Docker, AWS, PostgreSQL"""

SAMPLE_JD = """Software Engineer — Backend Platform
TechCorp | San Francisco, CA

We are looking for a Backend Platform Engineer.

Requirements:
• 4+ years of backend engineering experience
• Proficiency in Python or Go
• Experience with Kubernetes and AWS
• Strong understanding of distributed systems"""


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def browser_context_args():
    """Extra browser context options."""
    return {"base_url": BASE_URL}


# ── Health ────────────────────────────────────────────────────────────────────

def test_health_endpoint(page: Page):
    """App is reachable and healthy."""
    resp = page.goto(f"{BASE_URL}/health")
    assert resp.status == 200
    assert "ok" in page.content()


# ── Home page loads ───────────────────────────────────────────────────────────

def test_home_page_loads(page: Page):
    page.goto(BASE_URL)
    expect(page).to_have_title("Resume Tailor — AI-Powered")
    expect(page.locator("#resumeInput")).to_be_visible()
    expect(page.locator("#jdInput")).to_be_visible()
    expect(page.locator("#tailorBtn")).to_be_visible()


def test_load_sample(page: Page):
    """Load Sample button populates both textareas."""
    page.goto(BASE_URL)
    page.click("button:has-text('Load Sample')")
    resume_val = page.input_value("#resumeInput")
    jd_val = page.input_value("#jdInput")
    assert len(resume_val) > 100
    assert len(jd_val) > 50


def test_validation_empty_inputs(page: Page):
    """Submitting with empty inputs shows validation errors."""
    page.goto(BASE_URL)
    page.click("#tailorBtn")
    expect(page.locator("#resumeErr")).to_have_text("Resume must be at least 100 characters.")
    expect(page.locator("#jdErr")).to_have_text("Job description must be at least 50 characters.")


# ── History page ──────────────────────────────────────────────────────────────

def test_history_page_loads(page: Page):
    page.goto(f"{BASE_URL}/history-page")
    expect(page.locator("body")).to_be_visible()


# ── Full tailor pipeline (requires real OPENAI_API_KEY) ───────────────────────

@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY", "").startswith("sk-test"),
    reason="Skipped: real OPENAI_API_KEY not set",
)
def test_tailor_pipeline_completes(page: Page):
    """
    Full end-to-end: fill inputs, click Tailor, wait for 'Done' status,
    verify tailored resume and cover letter are populated.
    """
    page.goto(BASE_URL)
    page.fill("#resumeInput", SAMPLE_RESUME)
    page.fill("#jdInput", SAMPLE_JD)
    page.click("#tailorBtn")

    # Wait up to 3 minutes for the pipeline to finish (LLM calls take time)
    expect(page.locator("#statusText")).to_have_text("Done! Review your results below.", timeout=180_000)

    # Tailored resume should be populated
    resume_text = page.locator("#resumeOutput").text_content()
    assert len(resume_text or "") > 100

    # Cover letter tab
    page.click("button:has-text('Cover Letter')")
    cover_text = page.locator("#coverOutput").text_content()
    assert len(cover_text or "") > 50

    # Score should be rendered
    score_text = page.locator("#scoreLabel").text_content()
    assert score_text not in ("—", "")

    # PDF download buttons should be visible
    expect(page.locator("#dlResumeBtn")).to_be_visible()
    expect(page.locator("#dlCoverBtn")).to_be_visible()


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY", "").startswith("sk-test"),
    reason="Skipped: real OPENAI_API_KEY not set",
)
def test_ideal_resume_generation(page: Page):
    """Generate ideal resume after tailoring and verify output."""
    page.goto(BASE_URL)
    page.fill("#resumeInput", SAMPLE_RESUME)
    page.fill("#jdInput", SAMPLE_JD)
    page.click("#tailorBtn")

    # Wait for tailoring to finish
    expect(page.locator("#statusText")).to_have_text("Done! Review your results below.", timeout=180_000)

    # Switch to ideal resume tab
    page.click("button:has-text('Ideal Resume')")
    page.click("#genIdealBtn")

    # Wait for ideal resume to appear (another LLM call)
    expect(page.locator("#idealResumeBox")).not_to_be_empty(timeout=120_000)

    ideal_text = page.locator("#idealResumeBox").text_content()
    assert len(ideal_text or "") > 100

    # Diff section should appear
    expect(page.locator("#idealDiffSection")).to_be_visible()
