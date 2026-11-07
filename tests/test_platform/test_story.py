"""
Unit & Integration Tests for The Agew Story Cultural & Historical Exhibition (GET /story)
"""

import pytest
from httpx import AsyncClient, ASGITransport
from src.platform.app import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_story_route_renders_successfully(client: AsyncClient):
    """Ensure the Agew Story exhibition renders with 200 OK and contains core editorial pillars."""
    response = await client.get("/story")
    assert response.status_code == 200
    html = response.text

    # Editorial Theme & Taglines (Case-insensitive check)
    html_upper = html.upper()
    assert "A PEOPLE. A LANGUAGE." in html_upper
    assert "A LIVING HERITAGE." in html_upper
    assert "A DIGITAL FUTURE." in html_upper
    assert "Injibara University" in html
    assert "Institute of Agaw Studies" in html
    assert "ISO 639-3" in html
    assert "awn" in html

    # Authentic Cultural & Visual Anchors
    assert "Ambassador Betty Adamu" in html
    assert "Gundo" in html
    assert "Agew Horsemen Association" in html
    assert "Agew Fereseñoch Mahber" in html
    assert "Zagwe Dynasty" in html

    # Authentic Researched Image Paths
    assert "/static/images/story/agew_woman_walking.jpg" in html
    assert "/static/images/story/agew_woman_portrait.jpg" in html
    assert "/static/images/story/agew_culture_model.jpg" in html
    assert "/static/images/story/zengena_lake_awi.jpg" in html
    assert "/static/images/story/agew_horseman_injibara.jpg" in html
    assert "/static/images/story/lalibela_zagwe_monolith.jpg" in html


@pytest.mark.asyncio
async def test_the_agew_story_alias_route(client: AsyncClient):
    """Verify alias route /the-agew-story also returns 200 OK."""
    response = await client.get("/the-agew-story")
    assert response.status_code == 200
    assert "A People. A Language." in response.text or "A PEOPLE. A LANGUAGE." in response.text.upper()


@pytest.mark.asyncio
async def test_story_contains_linguistic_specimens(client: AsyncClient):
    """Verify dual orthographies (Latin and Ge'ez) and interlinear glosses."""
    response = await client.get("/story")
    assert response.status_code == 200
    html = response.text

    # Latin specimens with special phonemes ɨ and ŋ
    assert "Awi agawxi qutɨrsɨ kɨda ŋa." in html
    assert "Kasa dɨnxɨwa bɨsta asha deshta aqwɨ." in html

    # Ge'ez specimens with Ethiopic-Cushitic extensions (ጙ)
    assert "አዊ አጋውሢ ቁትርስ ክዳ ጙ።" in html

    # Gloss and translation
    assert "The language of the Awi Agaw endures." in html


@pytest.mark.asyncio
async def test_story_contains_tokenizer_comparison(client: AsyncClient):
    """Verify the computational linguistics tokenizer penalty comparison."""
    response = await client.get("/story")
    assert response.status_code == 200
    html = response.text

    assert "Tokenization Tax" in html
    assert "Generic Multilingual" in html
    assert "SentencePiece BPE" in html
    assert "&lt;0xC9&gt;" in html or "<0xC9>" in html


@pytest.mark.asyncio
async def test_story_contains_action_pathways(client: AsyncClient):
    """Ensure all 4 contribution pathways link to active platform endpoints."""
    response = await client.get("/story")
    assert response.status_code == 200
    html = response.text

    assert 'href="/ingest"' in html
    assert 'href="/review"' in html
    assert 'href="/export"' in html
    assert ('href="/auth/register"' in html or 'href="/"' in html)


@pytest.mark.asyncio
async def test_navbar_contains_agew_story_link(client: AsyncClient):
    """Ensure navigation bar across the platform includes 'The Agew Story' link."""
    # Check homepage
    home_resp = await client.get("/")
    assert home_resp.status_code == 200
    assert 'href="/story"' in home_resp.text
    assert "The Agew Story" in home_resp.text

    # Check story page itself
    story_resp = await client.get("/story")
    assert story_resp.status_code == 200
    assert 'href="/story"' in story_resp.text
