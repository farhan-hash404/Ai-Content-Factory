import os
import sys
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add parent directory to sys.path
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

from Graph.agents.multimedia import _generate_image_openai_dalle

def test_generate_image_openai_dalle_default_model():
    """Verify default dall-e-3 generation."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "mock_key"}):
        mock_client = MagicMock()
        calls = []
        
        def mock_generate(**kwargs):
            calls.append(kwargs)
            mock_response = MagicMock()
            img_obj = MagicMock()
            img_obj.b64_json = None
            img_obj.url = "http://example.com/image.png"
            mock_response.data = [img_obj]
            return mock_response
            
        mock_client.images.generate = mock_generate
        
        with patch("openai.OpenAI", return_value=mock_client), \
             patch("urllib.request.urlopen") as mock_urlopen:
             
            mock_resp_obj = MagicMock()
            mock_resp_obj.read.return_value = b"fake_image_bytes"
            mock_urlopen.return_value.__enter__.return_value = mock_resp_obj
            
            result = _generate_image_openai_dalle("test prompt")
            
            assert result == b"fake_image_bytes"
            assert len(calls) == 1
            assert calls[0]["model"] == "dall-e-3"
            assert calls[0]["quality"] == "standard"

def test_generate_image_openai_dalle_custom_model():
    """Verify that custom model and size parameters are passed directly."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "mock_key"}):
        mock_client = MagicMock()
        calls = []
        
        def mock_generate(**kwargs):
            calls.append(kwargs)
            mock_response = MagicMock()
            img_obj = MagicMock()
            img_obj.b64_json = None
            img_obj.url = "http://example.com/image.png"
            mock_response.data = [img_obj]
            return mock_response
            
        mock_client.images.generate = mock_generate
        
        with patch("openai.OpenAI", return_value=mock_client), \
             patch("urllib.request.urlopen") as mock_urlopen:
             
            mock_resp_obj = MagicMock()
            mock_resp_obj.read.return_value = b"fake_image_bytes"
            mock_urlopen.return_value.__enter__.return_value = mock_resp_obj
            
            result = _generate_image_openai_dalle("test prompt", model="dall-e-2", size="1024x1024")
            
            assert result == b"fake_image_bytes"
            assert len(calls) == 1
            assert calls[0]["model"] == "dall-e-2"
            assert "quality" not in calls[0]



class TestImageProviderChain:
    """The image chain must never leave a figure slot empty.

    A missing image renders as a broken-image icon in the UI and in every
    export, which reads as a bug rather than as a degraded provider. These pin
    the two links added for that reason, plus the ordering rule they rest on.
    """

    def test_search_query_strips_art_direction_from_the_prompt(self):
        """Stock search is keyword-based; a paragraph of art direction returns nothing."""
        from Graph.agents.multimedia import _search_query_from_prompt

        query = _search_query_from_prompt(
            "A sleek clean modern professional cinematic render depicting a "
            "high-dimensional vector embedding space, blue palette, minimalist "
            "style, photorealistic high quality lighting"
        )
        words = query.lower().split()
        assert len(words) <= 4, f"query too long for a stock search: {query!r}"
        for filler in ("clean", "modern", "professional", "illustration", "sleek",
                       "minimal", "minimalist", "style", "quality", "palette",
                       "render", "cinematic", "photorealistic", "lighting",
                       "a", "the"):
            assert filler not in words, f"{filler!r} survived into {query!r}"
        assert any(w in words for w in ("high-dimensional", "vector", "embedding", "space"))

    def test_search_query_never_returns_empty(self):
        """An unusable prompt must still produce a searchable term."""
        from Graph.agents.multimedia import _search_query_from_prompt

        for prompt in ("", "   ", "a the of and", "!!! ???"):
            assert _search_query_from_prompt(prompt).strip()

    def test_local_figure_renders_without_network_or_credentials(self, monkeypatch):
        """The final link cannot be allowed to depend on anything external."""
        from Graph.agents.multimedia import _render_figure_locally

        # Any outbound request here would be a design error, so make one fatal.
        import urllib.request
        monkeypatch.setattr(
            urllib.request, "urlopen",
            lambda *a, **k: pytest.fail("the local renderer must not use the network"),
        )
        monkeypatch.delenv("PEXELS_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        data = _render_figure_locally("An isometric diagram of a vector database")
        assert data, "the offline renderer must always produce an image"
        assert data[:8] == b"\x89PNG\r\n\x1a\n", "expected a PNG"

    def test_local_figure_colour_is_stable_for_the_same_prompt(self):
        """A figure that changes colour on every regeneration looks like a glitch."""
        from Graph.agents.multimedia import _render_figure_locally

        assert _render_figure_locally("same prompt") == _render_figure_locally("same prompt")

    def test_pexels_is_skipped_when_the_key_is_the_placeholder(self, monkeypatch):
        """.env.example ships `your-pexels-key-here`; that must not become a request."""
        from Graph.agents import multimedia

        monkeypatch.setenv("PEXELS_API_KEY", "your-pexels-key-here")
        import urllib.request
        monkeypatch.setattr(
            urllib.request, "urlopen",
            lambda *a, **k: pytest.fail("a placeholder key must not reach the network"),
        )
        assert multimedia._fetch_pexels_photo("anything") is None

    def test_pexels_request_sends_a_browser_user_agent(self):
        """Pexels answers 403 to urllib's default UA — which looks like a bad key."""
        import inspect
        from Graph.agents import multimedia

        src = inspect.getsource(multimedia._fetch_pexels_photo)
        assert "User-Agent" in src, (
            "without a browser User-Agent, Pexels returns 403 Forbidden and the "
            "photo fallback silently never works"
        )

    def test_selected_model_chooses_the_start_not_the_only_provider(self, monkeypatch):
        """A free-tier run must still reach the free tail after a paid provider fails."""
        from Graph.agents import multimedia

        calls = []
        monkeypatch.setattr(multimedia, "_generate_image_openai_dalle",
                            lambda *a, **k: calls.append("dalle") or None)
        monkeypatch.setattr(multimedia, "_generate_image_bytes_google",
                            lambda *a, **k: calls.append("gemini") or None)
        monkeypatch.setattr(multimedia, "_generate_image_pollinations",
                            lambda *a, **k: calls.append("pollinations") or None)
        monkeypatch.setattr(multimedia, "_fetch_pexels_photo",
                            lambda *a, **k: calls.append("pexels") or None)
        monkeypatch.setattr(multimedia, "_render_figure_locally",
                            lambda *a, **k: calls.append("local") or b"PNGDATA")

        assert multimedia._generate_image_multi_provider("x", model="dall-e-3") == b"PNGDATA"
        assert calls == ["dalle", "gemini", "pollinations", "pexels", "local"]

    def test_free_selection_skips_the_paid_providers_entirely(self, monkeypatch):
        """Trying DALL-E with no OpenAI credit is a round-trip that cannot succeed."""
        from Graph.agents import multimedia

        calls = []
        monkeypatch.setattr(multimedia, "_generate_image_openai_dalle",
                            lambda *a, **k: calls.append("dalle") or None)
        monkeypatch.setattr(multimedia, "_generate_image_bytes_google",
                            lambda *a, **k: calls.append("gemini") or None)
        monkeypatch.setattr(multimedia, "_generate_image_pollinations",
                            lambda *a, **k: calls.append("pollinations") or b"IMG")

        assert multimedia._generate_image_multi_provider("x", model="pollinations-turbo") == b"IMG"
        assert calls == ["pollinations"], f"paid providers were contacted: {calls}"
