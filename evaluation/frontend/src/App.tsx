import { useState, useCallback } from "react";
import { Layout } from "./components/Layout";
import { EvalConfigForm } from "./components/EvalConfigForm";
import { ConversationView } from "./components/ConversationView";
import { ResultsDashboard } from "./components/ResultsDashboard";
import { startEvaluation } from "./api";
import type {
  AppState,
  RunEvalRequest,
  ConversationTurn,
  EvalResult,
} from "./types";

export default function App() {
  const [appState, setAppState] = useState<AppState>("config");
  const [turns, setTurns] = useState<ConversationTurn[]>([]);
  const [result, setResult] = useState<EvalResult | null>(null);
  const [isJudging, setIsJudging] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const handleSubmit = useCallback(async (request: RunEvalRequest) => {
    setAppState("running");
    setTurns([]);
    setResult(null);
    setIsJudging(false);
    setErrorMsg("");

    await startEvaluation(request, {
      onStart: () => {},
      onTurn: (turn) => {
        setTurns((prev) => [...prev, turn]);
      },
      onJudging: () => {
        setIsJudging(true);
      },
      onResult: (evalResult) => {
        setIsJudging(false);
        setResult(evalResult);
        setAppState("completed");
      },
      onError: (error) => {
        setErrorMsg(error);
        setAppState("error");
      },
      onDone: () => {
        setIsJudging(false);
      },
    });
  }, []);

  const handleReset = useCallback(() => {
    setAppState("config");
    setTurns([]);
    setResult(null);
    setErrorMsg("");
  }, []);

  return (
    <Layout>
      {appState === "config" && <EvalConfigForm onSubmit={handleSubmit} />}

      {(appState === "running" || appState === "error") && (
        <div className="space-y-6">
          <ConversationView
            turns={turns}
            isRunning={appState === "running" && !isJudging}
            isJudging={isJudging}
          />

          {appState === "error" && (
            <div className="p-4 rounded-xl bg-danger-400/10 border border-danger-400/20 animate-fade-in">
              <p className="text-sm text-danger-400 font-medium mb-1">
                Evaluation Error
              </p>
              <p className="text-sm text-surface-300">{errorMsg}</p>
              <button
                onClick={handleReset}
                className="mt-3 px-4 py-2 rounded-lg border border-surface-700 text-surface-300 text-sm font-medium hover:bg-surface-800 transition-colors"
              >
                Go Back
              </button>
            </div>
          )}
        </div>
      )}

      {appState === "completed" && result && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div>
            <h3 className="text-sm font-semibold text-surface-400 uppercase tracking-wide mb-4">
              Conversation Transcript
            </h3>
            <ConversationView
              turns={turns}
              isRunning={false}
              isJudging={false}
            />
          </div>
          <div>
            <ResultsDashboard
              result={result}
              turns={turns}
              onReset={handleReset}
            />
          </div>
        </div>
      )}
    </Layout>
  );
}
