import {
  CheckCircle2,
  XCircle,
  RotateCcw,
  Trophy,
  BarChart3,
} from "lucide-react";
import type { EvalResult, ConversationTurn } from "../types";

interface Props {
  result: EvalResult;
  turns: ConversationTurn[];
  onReset: () => void;
}

function ScoreBar({ label, score }: { label: string; score: number }) {
  const pct = Math.round(score * 100);
  const color =
    score >= 0.8
      ? "bg-success-400"
      : score >= 0.5
        ? "bg-warning-400"
        : "bg-danger-400";

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="text-surface-300 capitalize">
          {label.replace(/_/g, " ")}
        </span>
        <span className="font-mono text-surface-200 font-medium">{pct}%</span>
      </div>
      <div className="h-2 rounded-full bg-surface-800 overflow-hidden">
        <div
          className={`h-full rounded-full ${color} transition-all duration-700 ease-out`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export function ResultsDashboard({ result, turns, onReset }: Props) {
  const totalTurns = turns.filter((t) => t.speaker === "evaluator").length;
  const avgLatency =
    turns.length > 0
      ? Math.round(
          turns.reduce((sum, t) => sum + (t.latency_ms || 0), 0) /
            turns.length,
        )
      : 0;

  const criteriaEntries = Object.entries(result.criteria_met || {});
  const criteriaMet = criteriaEntries.filter(([, v]) => v).length;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div
            className={`w-10 h-10 rounded-xl flex items-center justify-center ${
              result.goal_reached
                ? "bg-success-400/20 text-success-400"
                : "bg-danger-400/20 text-danger-400"
            }`}
          >
            <Trophy size={20} />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-surface-50">
              Evaluation Results
            </h2>
            <p className="text-sm text-surface-400">
              {totalTurns} turns &middot; {avgLatency}ms avg latency
            </p>
          </div>
        </div>
        <button
          onClick={onReset}
          className="flex items-center gap-2 px-4 py-2 rounded-lg border border-surface-700 text-surface-300 text-sm font-medium hover:bg-surface-800 transition-colors"
        >
          <RotateCcw size={14} />
          Run Again
        </button>
      </div>

      {/* Goal status */}
      <div
        className={`p-4 rounded-xl border ${
          result.goal_reached
            ? "bg-success-400/5 border-success-400/20"
            : "bg-danger-400/5 border-danger-400/20"
        }`}
      >
        <div className="flex items-center gap-2 mb-2">
          {result.goal_reached ? (
            <CheckCircle2 size={18} className="text-success-400" />
          ) : (
            <XCircle size={18} className="text-danger-400" />
          )}
          <span
            className={`font-semibold ${
              result.goal_reached ? "text-success-400" : "text-danger-400"
            }`}
          >
            {result.goal_reached ? "Goal Reached" : "Goal Not Reached"}
          </span>
        </div>
        {result.assessment && (
          <p className="text-sm text-surface-300 leading-relaxed">
            {result.assessment}
          </p>
        )}
      </div>

      {/* Scores */}
      <div className="p-5 rounded-xl bg-surface-900 border border-surface-800">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 size={16} className="text-surface-400" />
          <h3 className="text-sm font-semibold text-surface-200 uppercase tracking-wide">
            Scores
          </h3>
        </div>
        <div className="space-y-3">
          {Object.entries(result.scores || {}).map(([key, value]) => (
            <ScoreBar key={key} label={key} score={value} />
          ))}
        </div>
      </div>

      {/* Criteria */}
      {criteriaEntries.length > 0 && (
        <div className="p-5 rounded-xl bg-surface-900 border border-surface-800">
          <h3 className="text-sm font-semibold text-surface-200 uppercase tracking-wide mb-3">
            Success Criteria ({criteriaMet}/{criteriaEntries.length} met)
          </h3>
          <div className="space-y-2">
            {criteriaEntries.map(([criterion, met]) => (
              <div key={criterion} className="flex items-start gap-2">
                {met ? (
                  <CheckCircle2
                    size={16}
                    className="text-success-400 mt-0.5 flex-shrink-0"
                  />
                ) : (
                  <XCircle
                    size={16}
                    className="text-danger-400 mt-0.5 flex-shrink-0"
                  />
                )}
                <span className="text-sm text-surface-300">{criterion}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
