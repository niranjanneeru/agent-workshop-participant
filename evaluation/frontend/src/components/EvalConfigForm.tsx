import { useState, useEffect } from "react";
import {
  Globe,
  Braces,
  Target,
  ChevronRight,
  Plus,
  Trash2,
  Sparkles,
  BookOpen,
} from "lucide-react";
import type { RunEvalRequest, AgentEndpointConfig, EvalGoalConfig, GoalPreset } from "../types";
import { PRESET_TEMPLATES } from "../types";

interface Props {
  onSubmit: (request: RunEvalRequest) => void;
}

export function EvalConfigForm({ onSubmit }: Props) {
  const [step, setStep] = useState<1 | 2 | 3>(1);

  const [agentConfig, setAgentConfig] = useState<AgentEndpointConfig>({
    endpoint_url: "http://platform:8081/api/chat/sync",
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body_template: {
      message: "$message",
      history: "$messages",
      user_id: 1,
      thread_id: "$thread_id",
    },
    response_path: "response",
  });

  const [goalConfig, setGoalConfig] = useState<EvalGoalConfig>({
    goal: "",
    success_criteria: [""],
    initial_context: "",
    evaluator_persona: "A curious user seeking help.",
    max_turns: 6,
  });

  const [evalName, setEvalName] = useState("Custom Evaluation");
  const [evaluatorModel, setEvaluatorModel] = useState("gpt-4.1-mini");

  const [goalPresets, setGoalPresets] = useState<GoalPreset[]>([]);

  useEffect(() => {
    fetch("/api/eval/presets")
      .then((res) => res.json())
      .then((data: GoalPreset[]) => setGoalPresets(data))
      .catch(() => {});
  }, []);

  const [headersText, setHeadersText] = useState(
    JSON.stringify(agentConfig.headers, null, 2),
  );
  const [bodyText, setBodyText] = useState(
    JSON.stringify(agentConfig.body_template, null, 2),
  );

  function applyPreset(index: number) {
    const preset = PRESET_TEMPLATES[index];
    const newConfig = {
      ...agentConfig,
      ...preset.config,
      headers: { ...agentConfig.headers, ...preset.config.headers },
    };
    setAgentConfig(newConfig);
    setHeadersText(JSON.stringify(newConfig.headers, null, 2));
    setBodyText(JSON.stringify(newConfig.body_template, null, 2));
  }

  function handleSubmit() {
    let parsedHeaders = agentConfig.headers;
    let parsedBody = agentConfig.body_template;
    try {
      parsedHeaders = JSON.parse(headersText);
    } catch { /* use existing */ }
    try {
      parsedBody = JSON.parse(bodyText);
    } catch { /* use existing */ }

    const filteredCriteria = goalConfig.success_criteria.filter(
      (c) => c.trim() !== "",
    );

    onSubmit({
      name: evalName,
      agent_config: {
        ...agentConfig,
        headers: parsedHeaders,
        body_template: parsedBody,
      },
      goal_config: {
        ...goalConfig,
        success_criteria: filteredCriteria.length > 0 ? filteredCriteria : ["Goal is achieved"],
      },
      evaluator_model: evaluatorModel,
      judge_model: evaluatorModel,
    });
  }

  const canProceedStep1 = agentConfig.endpoint_url.trim() !== "" && agentConfig.response_path.trim() !== "";
  const canProceedStep2 =
    goalConfig.goal.trim() !== "" &&
    goalConfig.max_turns >= 1 &&
    goalConfig.max_turns <= 10;

  return (
    <div className="animate-fade-in">
      {/* Step indicators */}
      <div className="flex items-center gap-2 mb-8">
        {[
          { num: 1, label: "Agent Endpoint", icon: Globe },
          { num: 2, label: "Evaluation Goal", icon: Target },
          { num: 3, label: "Review & Run", icon: Sparkles },
        ].map(({ num, label, icon: Icon }, idx) => (
          <div key={num} className="flex items-center gap-2">
            {idx > 0 && (
              <ChevronRight size={16} className="text-surface-600 mx-1" />
            )}
            <button
              onClick={() => setStep(num as 1 | 2 | 3)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                step === num
                  ? "bg-accent-600/20 text-accent-400"
                  : step > num
                    ? "text-success-400 hover:bg-surface-800"
                    : "text-surface-400 hover:bg-surface-800"
              }`}
            >
              <Icon size={16} />
              {label}
            </button>
          </div>
        ))}
      </div>

      {/* Step 1: Agent Endpoint */}
      {step === 1 && (
        <div className="space-y-6 animate-fade-in">
          <div>
            <h2 className="text-xl font-semibold text-surface-50 mb-1">
              Configure Target Agent
            </h2>
            <p className="text-sm text-surface-400">
              Point us to your agent's HTTP endpoint. We'll chat with it to evaluate its performance.
            </p>
          </div>

          {/* Presets */}
          <div>
            <label className="block text-sm font-medium text-surface-300 mb-2">
              Quick Presets
            </label>
            <div className="flex gap-2 flex-wrap">
              {PRESET_TEMPLATES.map((preset, idx) => (
                <button
                  key={preset.name}
                  onClick={() => applyPreset(idx)}
                  className="px-3 py-1.5 rounded-lg border border-surface-700 text-sm text-surface-300 hover:border-accent-500 hover:text-accent-400 transition-colors"
                >
                  {preset.name}
                </button>
              ))}
            </div>
          </div>

          {/* Endpoint URL */}
          <div>
            <label className="block text-sm font-medium text-surface-300 mb-1.5">
              Endpoint URL *
            </label>
            <input
              type="url"
              placeholder="https://api.example.com/v1/chat/completions"
              value={agentConfig.endpoint_url}
              onChange={(e) =>
                setAgentConfig({ ...agentConfig, endpoint_url: e.target.value })
              }
              className="w-full px-4 py-2.5 rounded-lg bg-surface-900 border border-surface-700 text-surface-100 placeholder-surface-500 focus:outline-none focus:border-accent-500 focus:ring-1 focus:ring-accent-500 font-mono text-sm"
            />
          </div>

          {/* Method */}
          <div>
            <label className="block text-sm font-medium text-surface-300 mb-1.5">
              HTTP Method
            </label>
            <select
              value={agentConfig.method}
              onChange={(e) =>
                setAgentConfig({ ...agentConfig, method: e.target.value })
              }
              className="px-4 py-2.5 rounded-lg bg-surface-900 border border-surface-700 text-surface-100 focus:outline-none focus:border-accent-500"
            >
              <option>POST</option>
              <option>PUT</option>
            </select>
          </div>

          {/* Headers */}
          <div>
            <label className="block text-sm font-medium text-surface-300 mb-1.5">
              Request Headers (JSON)
            </label>
            <textarea
              rows={4}
              value={headersText}
              onChange={(e) => setHeadersText(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg bg-surface-900 border border-surface-700 text-surface-100 placeholder-surface-500 focus:outline-none focus:border-accent-500 focus:ring-1 focus:ring-accent-500 font-mono text-sm resize-none"
              spellCheck={false}
            />
          </div>

          {/* Body Template */}
          <div>
            <label className="block text-sm font-medium text-surface-300 mb-1.5">
              Request Body Template (JSON)
            </label>
            <p className="text-xs text-surface-500 mb-2">
              Use <code className="text-accent-400">$message</code> for the
              latest message,{" "}
              <code className="text-accent-400">$messages</code> for the full
              conversation history (OpenAI format),{" "}
              <code className="text-accent-400">$session_id</code> /{" "}
              <code className="text-accent-400">$thread_id</code> for a unique
              session/thread ID.
            </p>
            <textarea
              rows={6}
              value={bodyText}
              onChange={(e) => setBodyText(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg bg-surface-900 border border-surface-700 text-surface-100 placeholder-surface-500 focus:outline-none focus:border-accent-500 focus:ring-1 focus:ring-accent-500 font-mono text-sm resize-none"
              spellCheck={false}
            />
          </div>

          {/* Response Path */}
          <div>
            <label className="block text-sm font-medium text-surface-300 mb-1.5">
              Response Path *
            </label>
            <p className="text-xs text-surface-500 mb-2">
              Dot-separated path to extract the assistant's reply from the JSON
              response. E.g.,{" "}
              <code className="text-accent-400">choices.0.message.content</code>
            </p>
            <input
              type="text"
              placeholder="choices.0.message.content"
              value={agentConfig.response_path}
              onChange={(e) =>
                setAgentConfig({
                  ...agentConfig,
                  response_path: e.target.value,
                })
              }
              className="w-full px-4 py-2.5 rounded-lg bg-surface-900 border border-surface-700 text-surface-100 placeholder-surface-500 focus:outline-none focus:border-accent-500 focus:ring-1 focus:ring-accent-500 font-mono text-sm"
            />
          </div>

          <div className="flex justify-end pt-2">
            <button
              onClick={() => setStep(2)}
              disabled={!canProceedStep1}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-accent-600 text-white font-medium text-sm hover:bg-accent-500 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Next: Define Goal
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Evaluation Goal */}
      {step === 2 && (
        <div className="space-y-6 animate-fade-in">
          <div>
            <h2 className="text-xl font-semibold text-surface-50 mb-1">
              Define Evaluation Goal
            </h2>
            <p className="text-sm text-surface-400">
              Our AI evaluator will act as a user, trying to achieve this goal
              by chatting with your agent.
            </p>
          </div>

          {/* Goal presets from YAML */}
          {goalPresets.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-surface-300 mb-2">
                <BookOpen size={14} className="inline mr-1.5" />
                Checkpoint Presets
              </label>
              <div className="flex gap-2 flex-wrap">
                {goalPresets.map((preset) => (
                  <button
                    key={preset.id}
                    onClick={() => {
                      setGoalConfig({
                        goal: preset.goal,
                        success_criteria: [...preset.success_criteria],
                        initial_context: preset.initial_context,
                        evaluator_persona: preset.evaluator_persona,
                        max_turns: preset.max_turns,
                      });
                      setEvalName(preset.name);
                    }}
                    title={preset.description}
                    className="px-3 py-1.5 rounded-lg border border-surface-700 text-sm text-surface-300 hover:border-accent-500 hover:text-accent-400 transition-colors"
                  >
                    {preset.name}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Goal */}
          <div>
            <label className="block text-sm font-medium text-surface-300 mb-1.5">
              Goal *
            </label>
            <textarea
              rows={3}
              placeholder="Get the agent to help compare LangChain and Langfuse, explaining what each does and how they differ..."
              value={goalConfig.goal}
              onChange={(e) =>
                setGoalConfig({ ...goalConfig, goal: e.target.value })
              }
              className="w-full px-4 py-2.5 rounded-lg bg-surface-900 border border-surface-700 text-surface-100 placeholder-surface-500 focus:outline-none focus:border-accent-500 focus:ring-1 focus:ring-accent-500 text-sm resize-none"
            />
          </div>

          {/* Success Criteria */}
          <div>
            <label className="block text-sm font-medium text-surface-300 mb-1.5">
              Success Criteria
            </label>
            <p className="text-xs text-surface-500 mb-2">
              Define what the agent must achieve. All criteria are checked during
              evaluation.
            </p>
            <div className="space-y-2">
              {goalConfig.success_criteria.map((criterion, idx) => (
                <div key={idx} className="flex gap-2">
                  <input
                    type="text"
                    placeholder={`Criterion ${idx + 1}...`}
                    value={criterion}
                    onChange={(e) => {
                      const updated = [...goalConfig.success_criteria];
                      updated[idx] = e.target.value;
                      setGoalConfig({
                        ...goalConfig,
                        success_criteria: updated,
                      });
                    }}
                    className="flex-1 px-4 py-2 rounded-lg bg-surface-900 border border-surface-700 text-surface-100 placeholder-surface-500 focus:outline-none focus:border-accent-500 focus:ring-1 focus:ring-accent-500 text-sm"
                  />
                  {goalConfig.success_criteria.length > 1 && (
                    <button
                      onClick={() => {
                        const updated = goalConfig.success_criteria.filter(
                          (_, i) => i !== idx,
                        );
                        setGoalConfig({
                          ...goalConfig,
                          success_criteria: updated,
                        });
                      }}
                      className="p-2 rounded-lg text-surface-500 hover:text-danger-400 hover:bg-surface-800 transition-colors"
                    >
                      <Trash2 size={16} />
                    </button>
                  )}
                </div>
              ))}
              <button
                onClick={() =>
                  setGoalConfig({
                    ...goalConfig,
                    success_criteria: [...goalConfig.success_criteria, ""],
                  })
                }
                className="flex items-center gap-1.5 text-sm text-accent-400 hover:text-accent-300 transition-colors"
              >
                <Plus size={14} /> Add criterion
              </button>
            </div>
          </div>

          {/* Persona */}
          <div>
            <label className="block text-sm font-medium text-surface-300 mb-1.5">
              Evaluator Persona
            </label>
            <input
              type="text"
              placeholder="A developer new to LLM tooling wanting practical advice"
              value={goalConfig.evaluator_persona}
              onChange={(e) =>
                setGoalConfig({
                  ...goalConfig,
                  evaluator_persona: e.target.value,
                })
              }
              className="w-full px-4 py-2.5 rounded-lg bg-surface-900 border border-surface-700 text-surface-100 placeholder-surface-500 focus:outline-none focus:border-accent-500 focus:ring-1 focus:ring-accent-500 text-sm"
            />
          </div>

          {/* Context */}
          <div>
            <label className="block text-sm font-medium text-surface-300 mb-1.5">
              Initial Context
            </label>
            <input
              type="text"
              placeholder="The user is evaluating LLM tooling for a new project..."
              value={goalConfig.initial_context}
              onChange={(e) =>
                setGoalConfig({
                  ...goalConfig,
                  initial_context: e.target.value,
                })
              }
              className="w-full px-4 py-2.5 rounded-lg bg-surface-900 border border-surface-700 text-surface-100 placeholder-surface-500 focus:outline-none focus:border-accent-500 focus:ring-1 focus:ring-accent-500 text-sm"
            />
          </div>

          {/* Max Turns + Model */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-surface-300 mb-1.5">
                Max Turns
              </label>
              <input
                type="number"
                min={1}
                max={10}
                value={goalConfig.max_turns}
                onChange={(e) => {
                  const v = parseInt(e.target.value);
                  setGoalConfig({
                    ...goalConfig,
                    max_turns: Number.isNaN(v) ? 1 : Math.min(10, Math.max(1, v)),
                  });
                }}
                className="w-full px-4 py-2.5 rounded-lg bg-surface-900 border border-surface-700 text-surface-100 focus:outline-none focus:border-accent-500 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-surface-300 mb-1.5">
                Evaluator Model
              </label>
              <select
                value={evaluatorModel}
                onChange={(e) => setEvaluatorModel(e.target.value)}
                className="w-full px-4 py-2.5 rounded-lg bg-surface-900 border border-surface-700 text-surface-100 focus:outline-none focus:border-accent-500 text-sm"
              >
                <option value="gpt-4.1-mini">gpt-4.1-mini</option>
                <option value="gpt-4.1">gpt-4.1</option>
                <option value="gpt-4.1-nano">gpt-4.1-nano</option>
                <option value="gpt-4o">gpt-4o</option>
                <option value="gpt-4o-mini">gpt-4o-mini</option>
              </select>
            </div>
          </div>

          <div className="flex justify-between pt-2">
            <button
              onClick={() => setStep(1)}
              className="px-5 py-2.5 rounded-lg border border-surface-700 text-surface-300 font-medium text-sm hover:bg-surface-800 transition-colors"
            >
              Back
            </button>
            <button
              onClick={() => setStep(3)}
              disabled={!canProceedStep2}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-accent-600 text-white font-medium text-sm hover:bg-accent-500 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Next: Review
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Review & Run */}
      {step === 3 && (
        <div className="space-y-6 animate-fade-in">
          <div>
            <h2 className="text-xl font-semibold text-surface-50 mb-1">
              Review & Run
            </h2>
            <p className="text-sm text-surface-400">
              Confirm your configuration and start the evaluation.
            </p>
          </div>

          {/* Eval Name */}
          <div>
            <label className="block text-sm font-medium text-surface-300 mb-1.5">
              Evaluation Name
            </label>
            <input
              type="text"
              value={evalName}
              onChange={(e) => setEvalName(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg bg-surface-900 border border-surface-700 text-surface-100 focus:outline-none focus:border-accent-500 focus:ring-1 focus:ring-accent-500 text-sm"
            />
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-surface-900 border border-surface-800">
              <div className="flex items-center gap-2 text-surface-300 mb-3">
                <Globe size={16} />
                <span className="text-sm font-medium">Agent Endpoint</span>
              </div>
              <div className="space-y-1 text-sm">
                <p className="font-mono text-accent-400 break-all">
                  {agentConfig.method} {agentConfig.endpoint_url || "Not set"}
                </p>
                <p className="text-surface-400">
                  Response path:{" "}
                  <code className="text-surface-300">
                    {agentConfig.response_path || "Not set"}
                  </code>
                </p>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-surface-900 border border-surface-800">
              <div className="flex items-center gap-2 text-surface-300 mb-3">
                <Target size={16} />
                <span className="text-sm font-medium">Evaluation Goal</span>
              </div>
              <p className="text-sm text-surface-200 mb-2 line-clamp-2">
                {goalConfig.goal || "Not set"}
              </p>
              <p className="text-xs text-surface-400">
                {goalConfig.success_criteria.filter((c) => c.trim()).length}{" "}
                criteria &middot; {goalConfig.max_turns} max turns &middot;{" "}
                {evaluatorModel}
              </p>
            </div>
          </div>

          {/* Body preview */}
          <div>
            <label className="block text-sm font-medium text-surface-300 mb-1.5">
              <Braces size={14} className="inline mr-1" />
              Request Body Preview
            </label>
            <pre className="p-4 rounded-lg bg-surface-900 border border-surface-800 text-sm font-mono text-surface-300 overflow-x-auto">
              {bodyText}
            </pre>
          </div>

          <div className="flex justify-between pt-2">
            <button
              onClick={() => setStep(2)}
              className="px-5 py-2.5 rounded-lg border border-surface-700 text-surface-300 font-medium text-sm hover:bg-surface-800 transition-colors"
            >
              Back
            </button>
            <button
              onClick={handleSubmit}
              className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-accent-600 text-white font-semibold text-sm hover:bg-accent-500 transition-colors shadow-lg shadow-accent-600/25"
            >
              <Sparkles size={16} />
              Run Evaluation
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
