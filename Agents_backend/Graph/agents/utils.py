import os
import re
import logging
import threading
from dotenv import load_dotenv

load_dotenv()

from pydantic import Field
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_openai import ChatOpenAI
from event_bus import emit as event_emit
from usage import UsageCallback

# One shared callback records token usage for every completion, including
# calls made through .with_structured_output(). Attaching it here means no
# call site needs to know about accounting. See usage.py.
_usage_cb = UsageCallback()

logger = logging.getLogger("blog_pipeline")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if os.getenv("DEBUG") else logging.INFO)

def _emit(*args, **kwargs):
    return event_emit(*args, **kwargs)

def _job(state) -> str:
    """Extract job ID from state (works for both State dict and payload dict)."""
    return state.get("_job_id", "")

def _safe_slug(title: str) -> str:
    """Creates a filename-safe slug from a string."""
    s = title.strip().lower()
    s = re.sub(r"[^a-z0-9 _-]+", "", s)
    s = re.sub(r"\s+", "_", s).strip("_")
    return s or "blog"

def truncate_for_eval(text: str, limit: int, label: str, job_id: str = "") -> tuple:
    """Clip `text` to `limit` characters and report whether anything was lost.

    Evaluators cap their input to bound cost, but they did so silently: a
    4,447-word article (39,025 characters) was audited on 77% of its text and
    graded by G-Eval on 64% of it, with nothing in the logs, the reports or the
    scores to say so. A score computed over two thirds of an article is not the
    same measurement as one computed over all of it, and a reader of those
    numbers had no way to know which they were looking at.

    This does not raise the limits — that would just move the cost. It makes the
    loss visible, so a truncated score can be reported as one.

    Returns (clipped_text, info) where info is suitable for storing alongside
    the scores:
        {"truncated": bool, "chars_evaluated": int,
         "chars_total": int, "coverage": float}
    """
    total = len(text or "")
    clipped = (text or "")[:limit]
    info = {
        "truncated": total > limit,
        "chars_evaluated": len(clipped),
        "chars_total": total,
        "coverage": round(len(clipped) / total, 4) if total else 1.0,
    }
    if info["truncated"]:
        logger.warning(
            f"⚠️ {label}: input truncated to {limit:,} of {total:,} characters "
            f"({info['coverage']:.0%} of the article). The resulting score does "
            f"NOT cover the whole text — report it as a partial measurement."
        )
        _emit(
            job_id, "system", "working",
            f"{label} evaluated {info['coverage']:.0%} of the article "
            f"({limit:,} of {total:,} characters).",
            info,
        )
    return clipped, info


# ---------------------------------------------------------------------------
# PROVIDER CONFIGURATION (OpenAI-compatible)
# ---------------------------------------------------------------------------
# Every chat client in this project is a `ChatOpenAI`, which is really an
# OpenAI-*protocol* client: point `base_url` somewhere else and the same object
# talks to any vendor that serves the same wire format. Google exposes exactly
# such a surface for the Gemini models, so the whole pipeline — including
# `.with_structured_output()`, which compiles to tool calling — runs on Gemini
# without a second client library and without touching any call site.
#
# Resolution order for the endpoint:
#   1. LLM_BASE_URL            — explicit override, any OpenAI-compatible host.
#   2. GOOGLE_API_KEY present  — Google's OpenAI compatibility endpoint.
#   3. neither                 — api.openai.com (the historical default).
#
# Resolution order for the credential: LLM_API_KEY, then the key belonging to
# whichever endpoint was selected.
#
# OPENAI_API_KEY is deliberately NOT reused as the Gemini credential. Several
# modules treat a non-empty OPENAI_API_KEY as "the OpenAI REST API is
# reachable" and call DALL-E, Whisper or TTS with it directly; handing them a
# Gemini key would turn an instant skip into a slow round-trip failure.

_GOOGLE_OPENAI_BASE = "https://generativelanguage.googleapis.com/v1beta/openai/"

_OPENAI_KEY = (os.getenv("OPENAI_API_KEY") or "").strip()
_GOOGLE_KEY = (os.getenv("GOOGLE_API_KEY") or "").strip()

_BASE_URL = (os.getenv("LLM_BASE_URL") or "").strip()
if not _BASE_URL and _GOOGLE_KEY and not _OPENAI_KEY:
    _BASE_URL = _GOOGLE_OPENAI_BASE

_IS_GOOGLE_ENDPOINT = "generativelanguage.googleapis.com" in _BASE_URL

# A ChatOpenAI cannot be constructed without *some* credential, and this module
# is imported by the API process, which must start even when no key is
# configured yet. The placeholder keeps import working; the first actual
# request then fails with an authentication error naming the provider, which is
# the right place to learn that a key is missing.
_API_KEY = (
    (os.getenv("LLM_API_KEY") or "").strip()
    or (_GOOGLE_KEY if _IS_GOOGLE_ENDPOINT else _OPENAI_KEY)
    or "missing-llm-api-key"
)

# Model defaults follow the endpoint. Asking api.openai.com for
# "gemini-2.5-flash" — or Google for "gpt-5-mini" — is a 404, so the default
# has to move with the base URL rather than being one hardcoded string.
if _IS_GOOGLE_ENDPOINT:
    _DEFAULT_FAST, _DEFAULT_QUALITY = "gemini-3.5-flash-lite", "gemini-3.5-flash"
else:
    _DEFAULT_FAST, _DEFAULT_QUALITY = "gpt-5-mini", "gpt-5-mini"

_FAST_MODEL = os.getenv("LLM_FAST_MODEL", _DEFAULT_FAST)
_QUALITY_MODEL = os.getenv("LLM_QUALITY_MODEL", _DEFAULT_QUALITY)

# The EVALUATION judge is configured separately from the production models.
#
# WHY: `llm_quality` drives five different things — the QA auditor, the revision
# agent, the podcast scripter, the get_llm() fallback, and (previously) the
# G-Eval judge. Repointing LLM_QUALITY_MODEL to get an independent judge would
# therefore also swap the QA auditor and the reviser, so any change in scores
# could not be attributed to the judge alone. That confound made the
# independent-judge experiment invalid.
#
# LLM_JUDGE_MODEL is read ONLY by Graph/agents/evaluation.py. It defaults to
# LLM_QUALITY_MODEL, so behaviour is unchanged unless it is explicitly set:
#
#     LLM_JUDGE_MODEL=gemini-2.5-pro RUN_GOLDEN_TESTS=1 pytest tests/golden -v -s
#
# Temperature is pinned to 0 (not 0.1) because a grader should be as
# reproducible as the API allows.
_JUDGE_MODEL = os.getenv("LLM_JUDGE_MODEL", _QUALITY_MODEL)

# ---------------------------------------------------------------------------
# REQUEST TIMEOUT
# ---------------------------------------------------------------------------
# Unset, langchain-openai inherits the OpenAI SDK's default 600-second read
# timeout and retries twice — so one wedged request could occupy a worker
# thread for THIRTY MINUTES with no log line and no way to tell it apart from
# a slow model. Pipeline runs execute in FastAPI's bounded thread pool, and
# jobs awaiting human approval already hold threads for up to 20 minutes, so a
# hung call compounds directly into API-wide starvation.
#
# 180s comfortably covers the slowest observed call (the QA audit reads 30k
# characters); with 2 retries the worst case is ~9 minutes instead of ~30.
# Raise LLM_REQUEST_TIMEOUT if a larger model legitimately needs longer.
_REQUEST_TIMEOUT = float(os.getenv("LLM_REQUEST_TIMEOUT", "180"))
_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "2"))

# ---------------------------------------------------------------------------
# CLIENT-SIDE RATE LIMITING
# ---------------------------------------------------------------------------
# The Gemini free tier allows 5 requests per minute PER MODEL. The orchestrator
# fans section writers out concurrently — a 7-section outline issues 7 requests
# at once — so an unthrottled free-tier run fails the moment writing starts:
#
#   429 RESOURCE_EXHAUSTED: Quota exceeded for metric
#   generativelanguage.googleapis.com/generate_content_free_tier_requests,
#   limit: 5, model: gemini-3.5-flash. Please retry in 37.1s.
#
# SDK retries do not rescue this. Their backoff is measured in low seconds
# while the quota window is a rolling minute, and every concurrent request
# retries into the same exhausted window. The fix has to be admission control
# on the way OUT, not retries on the way back.
#
# `InMemoryRateLimiter` is a blocking token bucket. The pipeline runs its
# writers in a thread pool, so blocking a worker thread until a token is free
# is exactly the desired behaviour — the run gets slower, not broken.
#
# One bucket PER MODEL, because the quota is per model: splitting
# LLM_FAST_MODEL and LLM_QUALITY_MODEL across two model ids therefore doubles
# the effective throughput.
#
# max_bucket_size defaults to 1 — strict spacing, no burst. A burst of 5
# followed by one more request 12 seconds later is 6 requests inside the same
# rolling minute, which is a 429; only even spacing is reliably under the cap.
#
# Set LLM_REQUESTS_PER_MINUTE=0 to disable throttling (correct on a paid tier,
# where it is pure latency).
_DEFAULT_RPM = "5" if _IS_GOOGLE_ENDPOINT else "0"
_REQUESTS_PER_MINUTE = float(os.getenv("LLM_REQUESTS_PER_MINUTE", _DEFAULT_RPM))
_RATE_LIMIT_BURST = float(os.getenv("LLM_RATE_LIMIT_BURST", "1"))

_rate_limiters: dict[str, "InMemoryRateLimiter"] = {}


def _rate_limiter_for(model: str):
    """Shared token bucket for `model`, or None when throttling is disabled.

    Cached per model id so every client built for that model contends for the
    same quota the API actually enforces.
    """
    if _REQUESTS_PER_MINUTE <= 0:
        return None
    limiter = _rate_limiters.get(model)
    if limiter is None:
        limiter = InMemoryRateLimiter(
            requests_per_second=_REQUESTS_PER_MINUTE / 60.0,
            check_every_n_seconds=0.5,
            max_bucket_size=_RATE_LIMIT_BURST,
        )
        _rate_limiters[model] = limiter
    return limiter


# ---------------------------------------------------------------------------
# CROSS-MODEL FAILOVER
# ---------------------------------------------------------------------------
# The rate limiter above handles the per-MINUTE quota. It cannot help with the
# per-DAY one, which on this free tier is brutally small:
#
#   429 RESOURCE_EXHAUSTED
#   quotaId: GenerateRequestsPerDayPerProjectPerModel-FreeTier
#   quotaValue: 20
#
# Twenty requests per day per model, while one complete run (route, research,
# plan, N section writers, QA, revise, keyword pass, campaign, podcast script,
# video script, two evaluation arms) issues well over thirty. No amount of
# waiting fixes that — the budget is gone until tomorrow.
#
# What DOES fix it: the quota is per model, and the endpoint serves many
# interchangeable models. Failing a quota-exhausted request over to the next
# model multiplies the daily budget by the size of the pool, and turns "the
# demo cannot run today" into "the demo ran, on a slightly different model".
#
# Which errors trigger a failover:
#   * per-DAY quota (429)  — the model is finished for the day; remember that
#     and stop sending it anything, so later calls skip a doomed round-trip.
#   * per-minute quota (429) and capacity errors (503 "high demand",
#     overloaded) — transient, but another model is usually faster than waiting
#     out the window, and the SDK has already exhausted its own retries by the
#     time the exception reaches here.
#
# Anything else — a bad request, an auth failure, a 404 for a retired model —
# is re-raised untouched. Those are not capacity problems and retrying them on
# another model only hides the real fault.
#
# The model actually used is reported by the API in the response, so usage.py
# attributes tokens to the model that served the request, not the one asked
# for; a cost table after a failover shows the substitution rather than hiding
# it.

_FALLBACK_MODELS = [
    m.strip() for m in (os.getenv("LLM_FALLBACK_MODELS") or "").split(",") if m.strip()
]

# Models known to be out of daily quota in THIS process. Not persisted: the
# quota resets on Google's clock, not ours, and a stale file would wrongly rule
# out a model that is available again.
_exhausted_models: set[str] = set()
_exhausted_lock = threading.Lock()


def _error_text(err: Exception) -> str:
    return f"{type(err).__name__}: {err}".lower()


def _is_daily_quota_error(err: Exception) -> bool:
    """True for the per-day quota specifically, which waiting cannot clear."""
    return "perdayper" in _error_text(err).replace(" ", "")


def _is_capacity_error(err: Exception) -> bool:
    """True for quota and capacity errors — the cases another model can serve."""
    text = _error_text(err)
    return any(
        marker in text
        for marker in (
            "resource_exhausted", "quota", "ratelimiterror", "rate limit",
            "429", "503", "high demand", "unavailable", "overloaded",
        )
    )


def _mark_exhausted(model: str) -> None:
    with _exhausted_lock:
        if model not in _exhausted_models:
            _exhausted_models.add(model)
            logger.warning(
                f"🚫 Model {model!r} has exhausted its daily free-tier quota. "
                f"Skipping it for the rest of this process."
            )


class FailoverChatOpenAI(ChatOpenAI):
    """A chat client that retries a quota-blocked request on another model.

    `_get_request_payload` builds `{**self._default_params, **kwargs}`, so a
    `model` passed through kwargs overrides the configured one for a single
    call. That is what makes the retry possible without mutating shared state —
    important, because section writers run concurrently on one client.
    """

    fallback_models: list[str] = Field(default_factory=list)

    def _candidates(self, requested: str) -> list[str]:
        """Models to try, in order, skipping any already known to be spent."""
        ordered = [requested, *self.fallback_models]
        seen: set[str] = set()
        out: list[str] = []
        with _exhausted_lock:
            spent = set(_exhausted_models)
        for model in ordered:
            if model and model not in seen and model not in spent:
                seen.add(model)
                out.append(model)
        # Everything is spent: fall back to the requested model so the caller
        # gets the API's own error rather than an empty-list crash from here.
        return out or [requested]

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        requested = kwargs.get("model") or self.model_name
        candidates = self._candidates(requested)
        first_error: Exception | None = None

        for idx, model in enumerate(candidates):
            if idx > 0:
                limiter = _rate_limiter_for(model)
                if limiter is not None:
                    limiter.acquire(blocking=True)
                logger.warning(f"🔁 Retrying on fallback model {model!r}.")
            try:
                return super()._generate(
                    messages, stop=stop, run_manager=run_manager,
                    **{**kwargs, "model": model},
                )
            except Exception as err:
                if _is_daily_quota_error(err):
                    _mark_exhausted(model)
                elif not _is_capacity_error(err):
                    raise
                first_error = first_error or err

        raise first_error

    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        requested = kwargs.get("model") or self.model_name
        candidates = self._candidates(requested)
        first_error: Exception | None = None

        for idx, model in enumerate(candidates):
            if idx > 0:
                limiter = _rate_limiter_for(model)
                if limiter is not None:
                    await limiter.aacquire(blocking=True)
                logger.warning(f"🔁 Retrying on fallback model {model!r}.")
            try:
                return await super()._agenerate(
                    messages, stop=stop, run_manager=run_manager,
                    **{**kwargs, "model": model},
                )
            except Exception as err:
                if _is_daily_quota_error(err):
                    _mark_exhausted(model)
                elif not _is_capacity_error(err):
                    raise
                first_error = first_error or err

        raise first_error


def make_chat_llm(model: str, temperature: float = 0.0) -> ChatOpenAI:
    """Build a chat client for `model` against the configured endpoint.

    Single place where an endpoint, a credential, the shared usage callback,
    the per-model rate limiter and the fallback pool are attached, so adding a
    provider never means auditing call sites.
    """
    kwargs = {
        "model": model,
        "temperature": temperature,
        "timeout": _REQUEST_TIMEOUT,
        "max_retries": _MAX_RETRIES,
        "callbacks": [_usage_cb],
        "api_key": _API_KEY,
    }
    if _BASE_URL:
        kwargs["base_url"] = _BASE_URL
    limiter = _rate_limiter_for(model)
    if limiter is not None:
        kwargs["rate_limiter"] = limiter
    if not _FALLBACK_MODELS:
        return ChatOpenAI(**kwargs)
    return FailoverChatOpenAI(
        fallback_models=[m for m in _FALLBACK_MODELS if m != model], **kwargs
    )


# Model-id prefixes each endpoint will actually serve. A request for a model
# the endpoint does not host fails mid-generation with an opaque 404, so an
# unrecognised `selected_model` from the UI is refused here and the configured
# default is used instead.
_OPENAI_PREFIXES = ("gpt-", "o1", "o3", "o4", "chatgpt-")
_GOOGLE_PREFIXES = ("gemini-", "models/gemini-", "learnlm", "gemma-")


def get_llm(state: dict = None, temperature: float = 0.0) -> ChatOpenAI:
    """Return a chat client for the model selected in state, if available.

    The model id must belong to the configured endpoint — a Gemini id sent to
    api.openai.com, or a GPT id sent to Google, is a 404. Anything
    unrecognised falls back to the configured default rather than blowing up
    mid-generation.
    """
    model_name = _QUALITY_MODEL
    allowed = _GOOGLE_PREFIXES if _IS_GOOGLE_ENDPOINT else _OPENAI_PREFIXES
    requested = state.get("selected_model") if isinstance(state, dict) else None
    if requested:
        if requested.startswith(allowed):
            model_name = requested
        else:
            logger.warning(
                f"Ignoring unsupported model {requested!r} — the configured "
                f"endpoint ({_BASE_URL or 'api.openai.com'}) serves "
                f"{allowed}. Falling back to {model_name!r}."
            )
    return make_chat_llm(model_name, temperature)


# ---------------------------------------------------------------------------
# A NOTE ON temperature
# ---------------------------------------------------------------------------
# The temperature arguments below are NOT honoured by every model.
# Reasoning-family models (the gpt-5 line) accept only their default sampling
# temperature, and langchain-openai drops the parameter silently rather than
# raising — the constructed client reports `temperature is None`:
#
#     ChatOpenAI(model="gpt-5-mini",  temperature=0.7).temperature  -> None
#     ChatOpenAI(model="gpt-4o-mini", temperature=0.7).temperature  -> 0.7
#
# The values are kept because they DO take effect on models that accept them —
# the Gemini models included — and because they document the intent of each
# role. tests/test_evaluation.py::TestTemperatureIsInertOnReasoningModels
# guards the gpt-5 behaviour so the finding is not silently rediscovered.
llm_fast = make_chat_llm(_FAST_MODEL, temperature=0)
llm_quality = make_chat_llm(_QUALITY_MODEL, temperature=0.1)
llm_judge = make_chat_llm(_JUDGE_MODEL, temperature=0)
# Planner LLM uses higher temperature so blog outlines vary across runs
# instead of converging on the same headings for the same topic.
llm_planner = make_chat_llm(_QUALITY_MODEL, temperature=0.7)

# Backward compat alias
llm = llm_fast

logger.info(
    f"LLM endpoint: {_BASE_URL or 'https://api.openai.com/v1'} | "
    f"fast={_FAST_MODEL} quality={_QUALITY_MODEL} judge={_JUDGE_MODEL} | "
    f"rate limit: {'off' if _REQUESTS_PER_MINUTE <= 0 else f'{_REQUESTS_PER_MINUTE:g}/min per model'}"
)
