"""
Tests for Graph/agents/utils.py — shared utility helpers.
"""
from unittest.mock import patch

import pytest
from langchain_openai import ChatOpenAI

from Graph.agents.utils import _safe_slug


class TestSafeSlug:
    """Tests for _safe_slug()."""

    def test_basic_conversion(self):
        assert _safe_slug("Hello World") == "hello_world"

    def test_strips_special_characters(self):
        assert _safe_slug("AI & Healthcare: The Future!") == "ai_healthcare_the_future"

    def test_handles_multiple_spaces(self):
        slug = _safe_slug("too   many    spaces")
        assert "  " not in slug  # no double underscores from collapsed spaces
        assert slug == "too_many_spaces"

    def test_returns_fallback_for_empty_string(self):
        assert _safe_slug("") == "blog"

    def test_returns_fallback_for_only_special_chars(self):
        assert _safe_slug("!@#$%^&*()") == "blog"

    def test_preserves_hyphens_and_underscores(self):
        slug = _safe_slug("my-topic_name")
        assert "my-topic_name" == slug


# ---------------------------------------------------------------------------
# Every model client must be bounded in time
# ---------------------------------------------------------------------------


class TestRequestTimeoutsAreConfigured:
    """Unset, langchain-openai inherits the OpenAI SDK's 600s read timeout and
    retries twice: one wedged request occupies a worker thread for ~30 minutes,
    indistinguishable in the logs from a slow model. Pipeline runs live in
    FastAPI's bounded thread pool, and jobs awaiting approval already hold
    threads for up to 20 minutes, so an unbounded call compounds into API-wide
    starvation.
    """

    def test_all_shared_clients_have_a_timeout(self):
        from Graph.agents import utils

        for name in ("llm_fast", "llm_quality", "llm_judge", "llm_planner"):
            client = getattr(utils, name)
            timeout = getattr(client, "request_timeout", None) or getattr(client, "timeout", None)
            assert timeout, f"{name} has no request timeout — worst case is unbounded"
            assert timeout == utils._REQUEST_TIMEOUT

    def test_get_llm_applies_the_timeout(self):
        from Graph.agents.utils import get_llm, _REQUEST_TIMEOUT

        client = get_llm()
        timeout = getattr(client, "request_timeout", None) or getattr(client, "timeout", None)
        assert timeout == _REQUEST_TIMEOUT

    def test_embeddings_client_is_bounded(self):
        """Semantic chunking embeds every sentence in one call — the largest request made."""
        from Graph.agents.document_ingest import get_embeddings_model
        from Graph.agents.utils import _REQUEST_TIMEOUT

        model = get_embeddings_model()
        timeout = getattr(model, "request_timeout", None) or getattr(model, "timeout", None)
        assert timeout == _REQUEST_TIMEOUT

    def test_timeout_is_overridable_by_environment(self, monkeypatch):
        """A slower model must be accommodatable without a code change."""
        import importlib
        from Graph.agents import utils

        monkeypatch.setenv("LLM_REQUEST_TIMEOUT", "45")
        reloaded = importlib.reload(utils)
        try:
            assert reloaded._REQUEST_TIMEOUT == 45.0
        finally:
            monkeypatch.delenv("LLM_REQUEST_TIMEOUT", raising=False)
            importlib.reload(utils)  # restore the shared module for other tests

    def test_no_module_builds_a_bare_unbounded_client(self):
        """Bare ChatOpenAI(...) bypasses the timeout; route through get_llm()."""
        import pathlib
        import re

        backend = pathlib.Path(__file__).resolve().parent.parent
        offenders = []
        for path in backend.rglob("*.py"):
            if "tests" in path.parts or path.name == "utils.py":
                continue
            for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if line.lstrip().startswith("#"):
                    continue
                if re.search(r"\bChatOpenAI\s*\(", line):
                    offenders.append(f"{path.relative_to(backend)}:{i}")

        assert not offenders, (
            "these construct ChatOpenAI directly and so inherit the SDK's "
            "600s default; use get_llm() instead:\n  " + "\n  ".join(offenders)
        )


class TestUsageAccounting:
    """Token/cost accounting must be accurate, thread-safe, and never fatal.

    The project previously had no instrumentation at all, so cost and latency
    claims could not be defended and were removed from the thesis. These pin the
    behaviour the replacement numbers will rest on.
    """

    def test_self_check_passes(self):
        import usage

        usage.demo()  # asserts internally; raises on any regression

    def test_callback_is_attached_to_every_client(self):
        from Graph.agents import utils
        from usage import UsageCallback

        for name in ("llm_fast", "llm_quality", "llm_judge", "llm_planner"):
            cbs = getattr(utils, name).callbacks or []
            assert any(isinstance(c, UsageCallback) for c in cbs), f"{name} is unmetered"

        cbs = utils.get_llm().callbacks or []
        assert any(isinstance(c, UsageCallback) for c in cbs)

    def test_embeddings_client_must_not_be_given_callbacks(self):
        """OpenAIEmbeddings has no `callbacks` field and does not reject one.

        Passing it does not raise — langchain-openai moves the value into
        `model_kwargs`, which is then serialised into the API request. That
        breaks every embedding call, so embedding spend is deliberately
        excluded from the usage totals rather than metered this way.
        """
        import inspect
        from langchain_openai import OpenAIEmbeddings
        from Graph.agents import document_ingest

        assert "callbacks" not in OpenAIEmbeddings.model_fields, (
            "OpenAIEmbeddings now supports callbacks — embeddings could be metered"
        )
        src = inspect.getsource(document_ingest.get_embeddings_model)
        code = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith("#"))
        assert "callbacks" not in code, (
            "callbacks passed to OpenAIEmbeddings would be forwarded to the API "
            "as a request parameter and break document ingestion"
        )

    def test_counts_survive_worker_threads(self):
        """LangGraph fans section writers out to threads; those must be counted.

        This is why accounting uses a locked global plus snapshot/delta rather
        than a contextvar — a contextvar does not follow execution into threads
        it did not create, which would silently omit the bulk of a run's spend.
        """
        import threading
        import usage
        from langchain_core.messages import AIMessage
        from langchain_core.outputs import ChatGeneration, LLMResult

        usage.reset()
        cb = usage.UsageCallback()

        def emit_one():
            msg = AIMessage(
                content="x",
                usage_metadata={"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
            )
            cb.on_llm_end(
                LLMResult(
                    generations=[[ChatGeneration(message=msg)]],
                    llm_output={"model_name": "gpt-5-mini"},
                )
            )

        before = usage.snapshot()
        threads = [threading.Thread(target=emit_one) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        d = usage.delta(before)
        assert d["total"]["calls"] == 20, "lost calls made on worker threads"
        assert d["total"]["input_tokens"] == 2000
        usage.reset()

    def test_accounting_failure_never_breaks_a_run(self):
        """A malformed response must be swallowed, not propagated into the graph."""
        import usage

        usage.UsageCallback().on_llm_end(object())          # no generations
        usage.UsageCallback().on_llm_end(None)              # not a result at all

    def test_price_override_via_environment(self, monkeypatch):
        import usage

        monkeypatch.setenv("LLM_PRICE_GPT_5_MINI", "1.00,4.00")
        assert usage._price_for("gpt-5-mini") == (1.00, 4.00)


class TestFreeTierQuotaHandling:
    """The free tier caps requests per minute AND per day, both per model.

    These two limits broke the pipeline in different ways and needed different
    fixes, so they are pinned separately:

      * Per MINUTE (5): the orchestrator writes sections concurrently, so an
        unthrottled 7-section outline fired 7 requests at once and everything
        past the fifth returned 429. Fixed by admission control — a blocking
        token bucket per model.
      * Per DAY (20): one complete run makes over thirty calls, so waiting
        cannot help. Fixed by failing the request over to another model, since
        the cap is per model and the endpoint serves many.
    """

    @pytest.fixture
    def throttled(self, monkeypatch):
        """Force throttling on, whatever the ambient .env says.

        Skipping when `LLM_REQUESTS_PER_MINUTE` is 0 would mean CI — which has
        no .env and therefore no throttling — never exercises the limiter at
        all, which is exactly where a regression would go unnoticed.
        """
        from Graph.agents import utils

        monkeypatch.setattr(utils, "_REQUESTS_PER_MINUTE", 5.0)
        monkeypatch.setattr(utils, "_RATE_LIMIT_BURST", 1.0)
        monkeypatch.setattr(utils, "_rate_limiters", {})
        return utils

    def test_rate_limiter_is_shared_per_model_not_per_client(self, throttled):
        """The API enforces one quota per model, so one bucket must serve all
        clients built for that model — otherwise N clients get N times the
        allowance and the cap is not respected."""
        a = throttled.make_chat_llm("gemini-3.6-flash")
        b = throttled.make_chat_llm("gemini-3.6-flash", temperature=0.7)
        c = throttled.make_chat_llm("gemini-3.5-flash-lite")

        assert a.rate_limiter is b.rate_limiter, "same model must share a bucket"
        assert a.rate_limiter is not c.rate_limiter, (
            "different models have independent quotas; sharing one bucket "
            "would throttle to half the available throughput"
        )

    def test_rate_limit_spacing_matches_the_quota(self, throttled):
        limiter = throttled._rate_limiter_for("gemini-3.6-flash")
        assert limiter.requests_per_second == pytest.approx(5.0 / 60.0)
        # A burst of 5 followed by one more request 12 seconds later is still 6
        # inside the same rolling minute — i.e. a 429. Only even spacing is safe.
        assert limiter.max_bucket_size <= 1, (
            "a burst larger than 1 can exceed a rolling-window quota"
        )

    def test_throttling_can_be_turned_off_for_a_paid_tier(self, monkeypatch):
        """On a paid tier the limiter is pure latency, so it must be disableable."""
        from Graph.agents import utils

        monkeypatch.setattr(utils, "_REQUESTS_PER_MINUTE", 0.0)
        monkeypatch.setattr(utils, "_rate_limiters", {})
        assert utils._rate_limiter_for("gemini-3.6-flash") is None
        assert utils.make_chat_llm("gemini-3.6-flash").rate_limiter is None

    def test_daily_quota_error_is_distinguished_from_the_per_minute_one(self):
        """Only the per-day error should retire a model for the process.

        A per-minute 429 clears on its own; blacklisting on one would throw away
        a model for the rest of the run over a few seconds of contention.
        """
        from Graph.agents import utils

        per_day = Exception(
            "Error code: 429 - RESOURCE_EXHAUSTED 'quotaId': "
            "'GenerateRequestsPerDayPerProjectPerModel-FreeTier', 'quotaValue': '20'"
        )
        per_minute = Exception(
            "Error code: 429 - RESOURCE_EXHAUSTED 'quotaId': "
            "'GenerateRequestsPerMinutePerProjectPerModel-FreeTier', 'quotaValue': '5'"
        )
        overloaded = Exception("Error code: 503 - This model is currently experiencing high demand")
        bad_request = Exception("Error code: 400 - invalid argument: unknown field 'foo'")

        assert utils._is_daily_quota_error(per_day)
        assert not utils._is_daily_quota_error(per_minute)

        # All three capacity problems are worth trying on another model.
        for err in (per_day, per_minute, overloaded):
            assert utils._is_capacity_error(err)
        # A malformed request is not; retrying it elsewhere only hides the bug.
        assert not utils._is_capacity_error(bad_request)

    def test_exhausted_models_are_dropped_from_the_candidate_list(self):
        """Once a model is spent, sending it anything is a wasted round-trip."""
        from Graph.agents import utils

        client = utils.FailoverChatOpenAI(
            model="model-a",
            api_key="test",
            fallback_models=["model-b", "model-c"],
        )
        assert client._candidates("model-a") == ["model-a", "model-b", "model-c"]

        with utils._exhausted_lock:
            utils._exhausted_models.add("model-a")
        try:
            assert client._candidates("model-a") == ["model-b", "model-c"]
        finally:
            with utils._exhausted_lock:
                utils._exhausted_models.discard("model-a")

    def test_all_models_spent_still_reaches_the_api(self):
        """With nothing left, the caller must get the API's own quota error.

        Returning an empty candidate list would instead raise an unrelated
        error from inside the failover code, hiding the real cause.
        """
        from Graph.agents import utils

        client = utils.FailoverChatOpenAI(
            model="model-a", api_key="test", fallback_models=["model-b"]
        )
        with utils._exhausted_lock:
            utils._exhausted_models.update({"model-a", "model-b"})
        try:
            assert client._candidates("model-a") == ["model-a"]
        finally:
            with utils._exhausted_lock:
                utils._exhausted_models.difference_update({"model-a", "model-b"})

    def test_failover_overrides_the_model_per_call_not_on_the_client(self):
        """Section writers share one client across threads.

        Rotating `self.model_name` to fail over would leak one request's
        substitution into every concurrent request. The override has to travel
        in the per-call payload, which works because `_get_request_payload`
        merges kwargs over the client's defaults.
        """
        import inspect
        from Graph.agents import utils

        src = inspect.getsource(utils.FailoverChatOpenAI._generate)
        assert '"model": model' in src, "the retry must pass the model per call"
        assert "self.model_name =" not in src, (
            "mutating the shared client is not thread-safe"
        )

    def test_a_non_capacity_error_is_not_retried_elsewhere(self):
        from Graph.agents import utils

        calls = []

        class Boom(utils.FailoverChatOpenAI):
            def _call_super(self, **kwargs):
                calls.append(kwargs["model"])
                raise ValueError("schema is wrong")

        client = Boom(model="model-a", api_key="test", fallback_models=["model-b"])
        # Patch the inherited implementation the override delegates to.
        with patch.object(
            ChatOpenAI, "_generate", side_effect=lambda *a, **k: client._call_super(**k)
        ):
            with pytest.raises(ValueError, match="schema is wrong"):
                client._generate([])

        assert calls == ["model-a"], (
            "a malformed request must fail immediately, not burn the whole pool"
        )
