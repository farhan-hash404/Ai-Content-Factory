"""
Tests for the research node's zero-evidence gate.

Regression target: the `closed_book_evergreen` golden run shipped 2,825 words
with router_mode="hybrid", evidence_count=0 and a READY verdict — a completely
ungrounded post that every downstream consumer (orchestrator prompt,
metadata.json, run README, golden harness) still reported as source-grounded.

`_research_result` is the single place both of research_node's return paths
converge, so the gate is tested there plus once end-to-end through the node.
"""

from unittest.mock import patch

from Graph.agents import research as research_mod
from Graph.agents.research import _research_result, research_node
from Graph.state import EvidenceItem


def _evidence(url: str = "https://example.com/a") -> EvidenceItem:
    return EvidenceItem(
        title="A source",
        url=url,
        snippet="A verifiable fact about the topic.",
        published_at=None,
        source="example.com",
    )


# ---------------------------------------------------------------------------
# _research_result — the gate itself
# ---------------------------------------------------------------------------


def test_downgrades_hybrid_to_closed_book_when_no_evidence():
    out = _research_result({"mode": "hybrid", "_job_id": ""}, [])
    assert out["evidence"] == []
    assert out["mode"] == "closed_book"
    assert out["needs_research"] is False


def test_downgrades_open_book_to_closed_book_when_no_evidence():
    out = _research_result({"mode": "open_book", "_job_id": ""}, [])
    assert out["mode"] == "closed_book"
    assert out["needs_research"] is False


def test_keeps_mode_when_evidence_was_found():
    out = _research_result({"mode": "hybrid", "_job_id": ""}, [_evidence()])
    assert "mode" not in out, "mode must not be touched when evidence exists"
    assert "needs_research" not in out
    assert len(out["evidence"]) == 1


def test_already_closed_book_is_left_alone():
    """No downgrade to apply — and no misleading 'downgraded' event."""
    out = _research_result({"mode": "closed_book", "_job_id": ""}, [])
    assert out == {"evidence": []}


def test_missing_mode_is_treated_as_closed_book():
    """A state with no mode key must not raise, and must not be downgraded."""
    out = _research_result({"_job_id": ""}, [])
    assert out == {"evidence": []}


def test_document_evidence_alone_preserves_grounded_mode():
    """Upload evidence with zero web hits is still grounding — don't downgrade."""
    out = _research_result({"mode": "hybrid", "_job_id": ""}, [_evidence("file://doc.pdf#p1")])
    assert "mode" not in out


# ---------------------------------------------------------------------------
# research_node — the wiring
# ---------------------------------------------------------------------------


def test_research_node_downgrades_when_every_search_returns_nothing():
    """The 'no raw results' early-return path must go through the gate."""
    state = {
        "topic": "How photosynthesis works",
        "mode": "hybrid",
        "queries": ["how photosynthesis works"],
        "recency_days": 3650,
        "_job_id": "",
    }
    with patch.object(research_mod, "_web_search", return_value=[]):
        out = research_node(state)

    assert out["evidence"] == []
    assert out["mode"] == "closed_book"
    assert out["needs_research"] is False


class TestSearchProviderFallback:
    """Research must degrade, not disappear, when Tavily is unavailable.

    Tavily was the only search provider, so a missing or exhausted key turned
    every open_book run into an ungrounded one — the post still shipped, just
    with no citations. DuckDuckGo needs no credential, so it is the safety net.
    """

    def test_tavily_is_preferred_when_it_returns_results(self, monkeypatch):
        """Tavily first: its results carry article text and a real published date."""
        from Graph.agents import research as research_mod

        calls = []
        monkeypatch.setattr(
            research_mod, "_tavily_search",
            lambda *a, **k: calls.append("tavily") or [{"title": "t", "url": "u", "snippet": "s"}],
        )
        monkeypatch.setattr(
            research_mod, "_duckduckgo_search",
            lambda *a, **k: calls.append("ddg") or [],
        )

        assert len(research_mod._web_search("q")) == 1
        assert calls == ["tavily"], "DuckDuckGo must not be called when Tavily answers"

    def test_duckduckgo_is_used_when_tavily_returns_nothing(self, monkeypatch):
        """Covers both a missing key and an exhausted quota — both return []."""
        from Graph.agents import research as research_mod

        monkeypatch.setattr(research_mod, "_tavily_search", lambda *a, **k: [])
        monkeypatch.setattr(
            research_mod, "_duckduckgo_search",
            lambda *a, **k: [{"title": "t", "url": "u", "snippet": "s", "source": "duckduckgo"}],
        )

        results = research_mod._web_search("q")
        assert len(results) == 1 and results[0]["source"] == "duckduckgo"

    def test_no_tavily_key_does_not_attempt_a_tavily_request(self, monkeypatch):
        from Graph.agents import research as research_mod

        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        assert research_mod._tavily_search("q") == []

    def test_recency_window_rounds_up_to_a_containing_bucket(self, monkeypatch):
        """DuckDuckGo has fixed time buckets, not a day count.

        Rounding DOWN would silently discard sources the router considered in
        scope, so each window must map to the tightest bucket that still
        CONTAINS it.
        """
        from Graph.agents import research as research_mod

        seen = {}

        class FakeDDGS:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def text(self, query, max_results=5, timelimit=None):
                seen["timelimit"] = timelimit
                return []

        import sys
        import types
        module = types.ModuleType("ddgs")
        module.DDGS = FakeDDGS
        monkeypatch.setitem(sys.modules, "ddgs", module)

        for days, expected in [(1, "d"), (7, "w"), (8, "m"), (31, "m"),
                               (90, "y"), (366, "y"), (3650, None)]:
            research_mod._duckduckgo_search("q", recency_days=days)
            assert seen["timelimit"] == expected, (
                f"{days} days mapped to {seen['timelimit']!r}, expected {expected!r}"
            )

    def test_missing_ddgs_package_is_not_fatal(self, monkeypatch):
        """The fallback is a safety net; its absence must not break research."""
        import builtins
        from Graph.agents import research as research_mod

        real_import = builtins.__import__

        def blocked(name, *args, **kwargs):
            if name == "ddgs":
                raise ImportError("no ddgs")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", blocked)
        assert research_mod._duckduckgo_search("q") == []
