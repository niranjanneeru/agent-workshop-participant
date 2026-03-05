export interface AgentEndpointConfig {
  endpoint_url: string;
  method: string;
  headers: Record<string, string>;
  body_template: Record<string, unknown>;
  response_path: string;
}

export interface EvalGoalConfig {
  goal: string;
  success_criteria: string[];
  initial_context: string;
  evaluator_persona: string;
  max_turns: number;
}

export interface RunEvalRequest {
  name: string;
  agent_config: AgentEndpointConfig;
  goal_config: EvalGoalConfig;
  evaluator_model: string;
  judge_model: string;
}

export interface ConversationTurn {
  turn_number: number;
  speaker: "evaluator" | "target";
  message: string;
  latency_ms: number;
}

export interface EvalScores {
  goal_completion: number;
  helpfulness: number;
  accuracy: number;
  coherence: number;
  efficiency: number;
}

export interface EvalResult {
  goal_reached: boolean;
  criteria_met: Record<string, boolean>;
  scores: EvalScores;
  assessment: string;
}

export type AppState = "config" | "running" | "completed" | "error";

export interface GoalPreset extends EvalGoalConfig {
  id: string;
  name: string;
  description: string;
}

export interface PresetTemplate {
  name: string;
  description: string;
  config: Partial<AgentEndpointConfig>;
}

export const PRESET_TEMPLATES: PresetTemplate[] = [
  {
    name: "KV Kart Platform",
    description: "Platform /api/chat/sync — requires user_id, thread_id, and history for multi-turn",
    config: {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      endpoint_url: "http://platform:8081/api/chat/sync",
      body_template: {
        message: "$message",
        history: "$messages",
        user_id: 1,
        thread_id: "$thread_id",
      },
      response_path: "response",
    },
  },
  {
    name: "OpenAI Compatible",
    description: "For endpoints following the OpenAI chat completions format",
    config: {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer YOUR_API_KEY",
      },
      body_template: {
        model: "gpt-4.1-mini",
        messages: "$messages",
      },
      response_path: "choices.0.message.content",
    },
  },
  {
    name: "Simple Chat",
    description: "For endpoints that accept a single message string",
    config: {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body_template: {
        message: "$message",
        session_id: "$session_id",
      },
      response_path: "response",
    },
  },
  {
    name: "Custom",
    description: "Start from scratch with a blank template",
    config: {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body_template: {},
      response_path: "",
    },
  },
];
