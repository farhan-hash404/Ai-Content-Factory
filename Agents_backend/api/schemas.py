from pydantic import BaseModel, Field


class GenerationConfig(BaseModel):
    """Every user-controlled setting required to reproduce a generation job."""

    tone: str = "professional"
    audience: str = "general"
    sections: int = 3
    keywords: list[str] = Field(default_factory=list)
    generate_podcast: bool = False
    generate_video: bool = False
    generate_campaign: bool = False
    generate_qa: bool = True
    generate_images: bool = False
    num_images: int = 0
    upload_id: str | None = None
    source_mode: str = "hybrid"
    # Defaults for a caller that sends neither field. The frontend always sends
    # both; the CLI and the golden harness rely on these. They name the free
    # providers so a run with no paid credential works out of the box —
    # Graph/agents/utils.py falls back to LLM_QUALITY_MODEL if the configured
    # endpoint does not serve this model id.
    selected_model: str = "gemini-3.1-flash-lite"
    image_model: str = "pollinations-flux"
    image_size: str = "1024x1024"
    image_quality: str = "standard"
    image_style: str = "vivid"
    export_formats: list[str] = Field(default_factory=lambda: ["html"])
    # Experiment control only. False makes every worker receive the full
    # evidence pool instead of its assigned slice — the control arm for the
    # evidence-distribution ablation. Leave True for normal generation.
    assign_evidence: bool = True


class CreateJobRequest(GenerationConfig):
    topic: str


class RevisePlanRequest(BaseModel):
    feedback: str


class UpdatePlanRequest(BaseModel):
    """Accepts a directly-edited plan from the frontend outline editor."""

    blog_title: str
    tone: str = "professional"
    audience: str = "general"
    tasks: list[dict]
