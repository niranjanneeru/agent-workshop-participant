"""
External Agent Evaluator
========================

Adapts the conversational evaluation engine to work with arbitrary
HTTP endpoints instead of only the built-in SimpleToolAgent.
"""

from __future__ import annotations

import copy
import json
import logging
import os
import time
from collections.abc import AsyncGenerator
from uuid import uuid4

import httpx
import openai

from .models import AgentEndpointConfig, EvalGoalConfig, TurnEvent

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_litellm_url = os.environ.get("LITELLM_URL", "")
_base_url = f"{_litellm_url}/v1" if _litellm_url else None

EVALUATOR_SYSTEM_PROMPT = """\
You are a HUMAN USER talking to an AI assistant (the "target"). You are NOT an assistant — \
you are the customer/user who needs help. Your job is to get help from the assistant to \
accomplish something you need.

GOAL: {goal}

SUCCESS CRITERIA — the target must satisfy ALL of these (you use these internally to know \
when you're done; never mention them in your messages):
{criteria}

YOUR PERSONA: {persona}
{initial_context}

The assistant already knows your identity; do not state your user ID in messages. Refer to "my order", "that order", or use order numbers when a real customer would.

CRITICAL RULES:
- You are the HUMAN, not the assistant. NEVER say things like "How can I assist you?", \
"How may I help?", or anything an AI assistant would say.
- Start with a natural human request or question, like a real customer would. \
Examples: "Hey, I need help with...", "Can you check my order?", "What's the status of my last order?"
- Write like a real person — casual, direct, sometimes incomplete sentences. \
Real users don't write perfectly formal messages.
- You are a real customer with a real need. Never think or write like you're running a test. \
Never mention "criteria", "evaluation", or "testing".
- React to the assistant's replies as a human would: confused if the answer is vague, \
relieved if it helps, slightly annoyed if it's wrong.
- If you didn't get what you need, ask a follow-up or clarify — like a real person would.
- If something seems wrong, say so naturally (e.g. "That doesn't sound right" or \
"I think you might have the wrong order") — don't act like a QA tester.
- If you're still stuck, rephrase or give more detail — as a frustrated but polite customer would.
- Keep messages concise and natural (1-3 sentences).
"""

EVALUATOR_RESPONSE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "evaluator_user_message",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "user_message": {
                    "type": "string",
                    "description": "The exact message the user would say to the assistant. Natural, casual, 1-3 sentences. No meta-commentary.",
                }
            },
            "required": ["user_message"],
            "additionalProperties": False,
        },
    },
}

JSON_OBJECT_RESPONSE_FORMAT = {"type": "json_object"}

JSON_OBJECT_FALLBACK_INSTRUCTION = 'Respond with valid JSON only, no other text. Format: {"user_message": "your message here"}'


def _extract_user_message(content: str | None) -> str:
    """Parse evaluator response and extract user_message. Fallback to raw content if needed."""
    if not content or not content.strip():
        return "I need help."
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict) and "user_message" in parsed:
            msg = str(parsed["user_message"]).strip()
            return msg if msg else "I need help."
    except (json.JSONDecodeError, TypeError):
        pass
    return content


JUDGE_SYSTEM_PROMPT = """\
You are a conversation evaluator. Given a multi-turn dialogue between a user and an AI assistant,
assess whether the assistant successfully helped the user reach their goal.

GOAL: {goal}

SUCCESS CRITERIA:
{criteria}

Evaluate the full conversation and respond in EXACTLY this JSON format (no markdown, no extra text):
{{
  "goal_reached": true/false,
  "criteria_met": {{
    "<criterion_1>": true/false,
    "<criterion_2>": true/false
  }},
  "scores": {{
    "goal_completion": <float 0.0-1.0>,
    "helpfulness": <float 0.0-1.0>,
    "accuracy": <float 0.0-1.0>,
    "coherence": <float 0.0-1.0>,
    "efficiency": <float 0.0-1.0>
  }},
  "assessment": "<2-3 sentence summary>"
}}

Scoring guide:
- goal_completion: Did the target fully achieve the user's goal? (1.0 = fully, 0.0 = not at all)
- helpfulness: How helpful were the responses? Did the target proactively offer useful information?
- accuracy: Were the target's statements factually correct?
- coherence: Did the conversation flow naturally? Did the target stay on topic?
- efficiency: How quickly did the target resolve the user's need? (1.0 = minimal turns needed)
"""


class ExternalAgentAdapter:
    """Calls an external agent endpoint over HTTP."""

    def __init__(self, config: AgentEndpointConfig):
        self.config = config
        self.session_id = str(uuid4())
        self.history: list[dict] = []

    async def send_message(self, message: str) -> str:
        self.history.append({"role": "user", "content": message})
        body = self._build_request_body(message)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.request(
                method=self.config.method,
                url=self.config.endpoint_url,
                headers=self.config.headers,
                json=body,
            )
            response.raise_for_status()

        data = response.json()
        reply = self._extract_response(data)
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def _build_request_body(self, message: str) -> dict:
        return self._replace_vars(copy.deepcopy(self.config.body_template), message)

    def _replace_vars(self, obj, message: str):
        if isinstance(obj, str):
            if obj == "$message":
                return message
            if obj == "$messages":
                return list(self.history)
            if obj == "$session_id" or obj == "$thread_id":
                return self.session_id
            return obj
        if isinstance(obj, dict):
            return {k: self._replace_vars(v, message) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._replace_vars(item, message) for item in obj]
        return obj

    def _extract_response(self, data) -> str:
        parts = self.config.response_path.split(".")
        current = data
        for part in parts:
            if isinstance(current, list):
                current = current[int(part)]
            elif isinstance(current, dict):
                if part.isdigit():
                    current = current.get(int(part), current.get(part))
                else:
                    current = current[part]
            else:
                raise ValueError(
                    f"Cannot traverse into {type(current)} with key '{part}'"
                )
        return str(current)


async def run_evaluation(
    agent_config: AgentEndpointConfig,
    goal_config: EvalGoalConfig,
    evaluator_model: str = "gpt-4.1-mini",
    judge_model: str = "gpt-4.1-mini",
) -> AsyncGenerator[TurnEvent, None]:
    """
    Generator that yields TurnEvent objects as the conversation progresses.
    The frontend connects via SSE and receives these in real time.
    """
    client = (
        openai.AsyncOpenAI(base_url=_base_url) if _base_url else openai.AsyncOpenAI()
    )
    adapter = ExternalAgentAdapter(agent_config)

    criteria_str = "\n".join(f"  - {c}" for c in goal_config.success_criteria)
    persona = goal_config.evaluator_persona or "A curious user seeking help."

    evaluator_system = EVALUATOR_SYSTEM_PROMPT.format(
        goal=goal_config.goal,
        criteria=criteria_str,
        persona=persona,
        initial_context=(
            f"CONTEXT: {goal_config.initial_context}"
            if goal_config.initial_context
            else ""
        ),
    )

    evaluator_messages: list[dict] = [{"role": "system", "content": evaluator_system}]
    turns: list[dict] = []

    try:
        for turn_num in range(goal_config.max_turns):
            # --- Evaluator generates a message ---
            eval_t0 = time.time()
            try:
                eval_response = await client.chat.completions.create(
                    model=evaluator_model,
                    temperature=0.3,
                    messages=evaluator_messages,
                    response_format=EVALUATOR_RESPONSE_SCHEMA,
                )
            except (openai.BadRequestError, openai.APIError):
                # Fallback for backends that don't support json_schema
                fallback_messages = [
                    *evaluator_messages,
                    {"role": "user", "content": JSON_OBJECT_FALLBACK_INSTRUCTION},
                ]
                eval_response = await client.chat.completions.create(
                    model=evaluator_model,
                    temperature=0.3,
                    messages=fallback_messages,
                    response_format=JSON_OBJECT_RESPONSE_FORMAT,
                )
            content = eval_response.choices[0].message.content
            eval_msg = _extract_user_message(content)
            eval_latency = (time.time() - eval_t0) * 1000

            turns.append({"speaker": "evaluator", "message": eval_msg})
            yield TurnEvent(
                type="turn",
                turn_number=turn_num + 1,
                speaker="evaluator",
                message=eval_msg,
                latency_ms=round(eval_latency, 1),
            )

            # --- Target agent responds ---
            target_t0 = time.time()
            try:
                target_reply = await adapter.send_message(eval_msg)
            except httpx.HTTPStatusError as exc:
                err_text = (exc.response.text or "")[:500]
                logger.warning(
                    "eval target HTTP error: %s %s body=%s",
                    exc.response.status_code,
                    getattr(exc.request, "url", ""),
                    err_text,
                )
                yield TurnEvent(
                    type="error",
                    error=f"Target endpoint returned {exc.response.status_code}: {err_text}",
                )
                return
            except Exception as exc:
                logger.warning("eval target request failed: %s", exc, exc_info=True)
                yield TurnEvent(type="error", error=f"Failed to reach target: {exc}")
                return

            target_latency = (time.time() - target_t0) * 1000
            reply_preview = (target_reply or "")[:300].replace("\n", " ")
            logger.info(
                "eval turn %s target reply (%sms): %s",
                turn_num + 1,
                round(target_latency, 0),
                reply_preview,
            )

            turns.append({"speaker": "target", "message": target_reply})
            yield TurnEvent(
                type="turn",
                turn_number=turn_num + 1,
                speaker="target",
                message=target_reply,
                latency_ms=round(target_latency, 1),
            )

            evaluator_messages.append({"role": "assistant", "content": eval_msg})
            evaluator_messages.append(
                {"role": "user", "content": f"[Target agent responded]: {target_reply}"}
            )

    except Exception as exc:
        yield TurnEvent(type="error", error=str(exc))
        return

    # --- Final judgment ---
    yield TurnEvent(type="judging", message="Evaluating conversation...")

    judgment = await _judge_conversation(
        client=client,
        judge_model=judge_model,
        goal=goal_config.goal,
        criteria=goal_config.success_criteria,
        turns=turns,
    )
    logger.info(
        "eval judge result: goal_reached=%s assessment=%s",
        judgment.get("goal_reached"),
        (judgment.get("assessment") or "")[:200],
    )

    yield TurnEvent(type="result", result=judgment)


async def _judge_conversation(
    client: openai.AsyncOpenAI,
    judge_model: str,
    goal: str,
    criteria: list[str],
    turns: list[dict],
) -> dict:
    criteria_str = "\n".join(f"  - {c}" for c in criteria)

    transcript_lines = []
    for turn in turns:
        role = "User" if turn["speaker"] == "evaluator" else "Assistant"
        transcript_lines.append(f"{role}: {turn['message']}")
    transcript = "\n".join(transcript_lines)

    judge_system = JUDGE_SYSTEM_PROMPT.format(goal=goal, criteria=criteria_str)

    try:
        response = await client.chat.completions.create(
            model=judge_model,
            temperature=0,
            messages=[
                {"role": "system", "content": judge_system},
                {
                    "role": "user",
                    "content": f"CONVERSATION TRANSCRIPT:\n\n{transcript}",
                },
            ],
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
        return json.loads(text)
    except (json.JSONDecodeError, Exception) as exc:
        return {
            "goal_reached": False,
            "criteria_met": {},
            "scores": {"goal_completion": 0.0},
            "assessment": f"Judge error: {exc}",
        }
