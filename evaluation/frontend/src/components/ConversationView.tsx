import { useEffect, useRef } from "react";
import { Bot, User, Loader2 } from "lucide-react";
import type { ConversationTurn } from "../types";

interface Props {
  turns: ConversationTurn[];
  isRunning: boolean;
  isJudging: boolean;
}

export function ConversationView({ turns, isRunning, isJudging }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns.length, isJudging]);

  return (
    <div className="animate-fade-in">
      <div className="flex items-center gap-3 mb-6">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2.5 w-2.5">
            {isRunning && (
              <span className="absolute inline-flex h-full w-full rounded-full bg-accent-400 opacity-75 animate-ping" />
            )}
            <span
              className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                isRunning ? "bg-accent-400" : isJudging ? "bg-warning-400" : "bg-success-400"
              }`}
            />
          </span>
          <span className="text-sm font-medium text-surface-300">
            {isRunning
              ? "Conversation in progress..."
              : isJudging
                ? "Judging conversation..."
                : "Conversation complete"}
          </span>
        </div>
        <span className="text-xs text-surface-500">
          {turns.length} message{turns.length !== 1 ? "s" : ""}
        </span>
      </div>

      <div className="space-y-4">
        {turns.map((turn, idx) => (
          <div
            key={idx}
            className={`flex gap-3 animate-fade-in ${
              turn.speaker === "evaluator" ? "" : ""
            }`}
          >
            <div
              className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center ${
                turn.speaker === "evaluator"
                  ? "bg-accent-600/20 text-accent-400"
                  : "bg-surface-800 text-surface-400"
              }`}
            >
              {turn.speaker === "evaluator" ? (
                <User size={16} />
              ) : (
                <Bot size={16} />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-medium text-surface-400 uppercase tracking-wide">
                  {turn.speaker === "evaluator"
                    ? "Evaluator"
                    : "Target Agent"}
                </span>
                <span className="text-xs text-surface-600">
                  Turn {turn.turn_number}
                </span>
                {turn.latency_ms > 0 && (
                  <span className="text-xs text-surface-600">
                    {turn.latency_ms.toFixed(0)}ms
                  </span>
                )}
              </div>
              <div
                className={`p-3 rounded-lg text-sm leading-relaxed ${
                  turn.speaker === "evaluator"
                    ? "bg-accent-600/10 border border-accent-600/20 text-surface-200"
                    : "bg-surface-900 border border-surface-800 text-surface-200"
                }`}
              >
                {turn.message}
              </div>
            </div>
          </div>
        ))}

        {(isRunning || isJudging) && (
          <div className="flex items-center gap-3 py-2 text-surface-400">
            <Loader2 size={16} className="animate-spin" />
            <span className="text-sm">
              {isJudging
                ? "AI judge is evaluating the conversation..."
                : "Waiting for next message..."}
            </span>
          </div>
        )}

        <div ref={scrollRef} />
      </div>
    </div>
  );
}
