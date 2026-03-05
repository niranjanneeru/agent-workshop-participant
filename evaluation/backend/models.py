from __future__ import annotations

from pydantic import BaseModel, Field


class AgentEndpointConfig(BaseModel):
    """Configuration for an external agent's HTTP endpoint."""

    endpoint_url: str = Field(..., description="The URL to call (e.g. https://api.example.com/chat)")
    method: str = Field(default="POST", description="HTTP method")
    headers: dict[str, str] = Field(default_factory=dict, description="Request headers")
    body_template: dict = Field(
        ...,
        description=(
            "JSON body template with special placeholders: "
            '"$message" → latest user message string, '
            '"$messages" → full conversation so far (list of {role, content}); use as history for multi-turn, '
            '"$session_id" / "$thread_id" → auto-generated session/thread ID per run'
        ),
    )
    response_path: str = Field(
        ...,
        description=(
            "Dot-separated path to extract the assistant reply from the JSON response. "
            'E.g. "choices.0.message.content" or "response"'
        ),
    )


class EvalGoalConfig(BaseModel):
    """What the evaluator agent should try to achieve."""

    goal: str = Field(..., description="The goal the evaluator should try to achieve")
    success_criteria: list[str] = Field(
        ..., min_length=1, description="Success criteria — all must be met"
    )
    initial_context: str = Field(default="", description="Context about the user scenario")
    evaluator_persona: str = Field(
        default="A curious user seeking help.",
        description="Persona the evaluator agent should adopt",
    )
    max_turns: int = Field(default=6, ge=1, le=10, description="Maximum conversation turns")


class RunEvalRequest(BaseModel):
    """Full request to start a custom evaluation."""

    name: str = Field(default="Custom Evaluation", description="Name for this evaluation run")
    agent_config: AgentEndpointConfig
    goal_config: EvalGoalConfig
    evaluator_model: str = Field(default="gpt-4.1-mini", description="Model for the evaluator agent")
    judge_model: str = Field(default="gpt-4.1-mini", description="Model for the final judge")


class PresetGoalConfig(EvalGoalConfig):
    """A named preset loaded from checkpoints.yaml."""

    id: str = Field(..., description="Unique identifier for the preset")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(default="", description="Short description of what this preset tests")


class TurnEvent(BaseModel):
    """A single conversation turn streamed to the frontend."""

    type: str  # "turn", "judging", "result", "error"
    turn_number: int | None = None
    speaker: str | None = None  # "evaluator" or "target"
    message: str | None = None
    latency_ms: float | None = None
    error: str | None = None
    result: dict | None = None
